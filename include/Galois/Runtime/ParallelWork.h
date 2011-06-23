// simple galois scheduler and runtime -*- C++ -*-
/*
Galois, a framework to exploit amorphous data-parallelism in irregular
programs.

Copyright (C) 2011, The University of Texas at Austin. All rights reserved.
UNIVERSITY EXPRESSLY DISCLAIMS ANY AND ALL WARRANTIES CONCERNING THIS SOFTWARE
AND DOCUMENTATION, INCLUDING ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR ANY
PARTICULAR PURPOSE, NON-INFRINGEMENT AND WARRANTIES OF PERFORMANCE, AND ANY
WARRANTY THAT MIGHT OTHERWISE ARISE FROM COURSE OF DEALING OR USAGE OF TRADE.
NO WARRANTY IS EITHER EXPRESS OR IMPLIED WITH RESPECT TO THE USE OF THE
SOFTWARE OR DOCUMENTATION. Under no circumstances shall University be liable
for incidental, special, indirect, direct or consequential damages or loss of
profits, interruption of business, or related expenses which may arise from use
of Software or Documentation, including but not limited to those resulting from
defects in Software and/or Documentation, or loss or inaccuracy of data of any
kind.
*/

#ifndef __PARALLELWORK_H_
#define __PARALLELWORK_H_
#include <algorithm>
#include <numeric>
#include <sstream>
#include <math.h>
#include "Galois/Executable.h"
#include "Galois/Mem.h"

#include "Galois/Runtime/Support.h"
#include "Galois/Runtime/Context.h"
#include "Galois/Runtime/Timer.h"
#include "Galois/Runtime/Threads.h"
#include "Galois/Runtime/PerCPU.h"
#include "Galois/Runtime/WorkList.h"
#include "Galois/Runtime/DebugWorkList.h"
#include "Galois/Runtime/Termination.h"

#ifdef GALOIS_VTUNE
#include "ittnotify.h"
#endif

namespace GaloisRuntime {

//Handle Runtime Conflict Detection
template<bool SRC_ACTIVE>
class SimpleRuntimeContextHandler;

template<>
class SimpleRuntimeContextHandler<true> {
  SimpleRuntimeContext src;
public:
  void start_iteration() {
    src.start_iteration();
  }
  void cancel_iteration() {
    src.cancel_iteration();
  }
  void commit_iteration() {
    src.commit_iteration();
  }
  void start_parallel_region() {
    setThreadContext(&src);
  }
  void end_parallel_region() {
    setThreadContext(0);
  }
};

template<>
class SimpleRuntimeContextHandler<false> {
public:
  void start_iteration() {}
  void cancel_iteration() {}
  void commit_iteration() {}
  void start_parallel_region() {}
  void end_parallel_region() {}
};

//Handle Statistic gathering
template<bool STAT_ACTIVE>
class StatisticHandler;

template<>
class StatisticHandler<true> {
  unsigned long conflicts;
  unsigned long iterations;
public:
  StatisticHandler() :conflicts(0), iterations(0) {}
  void inc_iterations() {
    ++iterations;
  }
  void inc_conflicts() {
    ++conflicts;
  }
  void report_stat() const {
    reportStat("Conflicts", conflicts);
    reportStat("Iterations", iterations);
  }
  void merge_stat(const StatisticHandler& rhs) {
    conflicts += rhs.conflicts;
    iterations += rhs.iterations;
  }
  struct stat_sum {
    std::vector<long> list;
    void add(StatisticHandler& x) {
      list.push_back(x.iterations);
    }
    void done() {
      GaloisRuntime::summarizeList("IterationDistribution", 
				   &list[0], &list[list.size()]);
    }
    int num() {
      return GaloisRuntime::getSystemThreadPool().getActiveThreads();
    }
  };
};

template<>
class StatisticHandler<false> {
public:
  void inc_iterations() {}
  void inc_conflicts() {}
  void report_stat() const {}
  void merge_stat(const StatisticHandler& rhs) {}
  struct stat_sum {
    void add(StatisticHandler& x) {}
    void done() {}
    int num() { return 0; }
  };
};


//Handle Parallel Pause
template<bool PAUSE_ACTIVE>
class API_Pause;
template<bool PAUSE_ACTIVE>
class PauseImpl;

template<>
class PauseImpl<true> {
  long atBarrier;
public:
  Galois::Executable* E;

  PauseImpl() :atBarrier(0), E(0) {}

  void handlePause(Galois::Executable* nE) {
    E = nE;
  }

  void checkPause() {
    if (E) {
      __sync_add_and_fetch(&atBarrier, 1);
      int numThreads = GaloisRuntime::getSystemThreadPool().getActiveThreads();
      while (atBarrier != numThreads) {}
      if (ThreadPool::getMyID() == 1) {
	E->operator()();
	E = 0;
      } else {
	while (E) {}
      }
    }
  }
};

template<>
class PauseImpl<false> {
public:
  void checkPause() {}
};

template<>
class API_Pause<true> {
  PauseImpl<true>* p;
protected:
  void init_pause(PauseImpl<true>* pi) {
    p = pi;
  }
public:
  void suspendWith(Galois::Executable* E) {
    p->handlePause(E);
  }
};
template<>
class API_Pause<false> {
};

//Handle Per Iter Allocator
template<bool PIA_ACTIVE>
class API_PerIter;

template<>
class API_PerIter<true>
{
  Galois::ItAllocBaseTy IterationAllocatorBase;
  Galois::PerIterAllocTy PerIterationAllocator;

protected:
  void __resetAlloc() {
    IterationAllocatorBase.clear();
  }

public:
  API_PerIter()
    :IterationAllocatorBase(), 
     PerIterationAllocator(&IterationAllocatorBase)
  {}

  virtual ~API_PerIter() {
    IterationAllocatorBase.clear();
  }

  Galois::PerIterAllocTy& getPerIterAlloc() {
    return PerIterationAllocator;
  }
};

template<>
class API_PerIter<false>
{
protected:
  void __resetAlloc() {}
};


//Handle Parallel Pause
template<bool PUSH_ACTIVE, typename WLT>
class API_Push;

template<typename WLT>
class API_Push<true, WLT> {
  typedef typename WLT::value_type value_type;
  WLT* wl;
protected:
  void init_wl(WLT* _wl) {
    wl = _wl;
  }
public:
  void push(const value_type& v) {
    wl->push(v);
  }
};

template<typename WLT>
class API_Push<false, WLT> {
protected:
  void init_wl(WLT* _wl) {}
};


template<typename Function>
struct Configurator {
  enum {
    CollectStats = 1,
    NeedsPause = 1,
    NeedsPush = 1,
    NeedsContext = 1,
    NeedsPIA = 1
  };
};

template<typename Function, class WorkListTy>
class ParallelThreadContext
  : public SimpleRuntimeContextHandler<Configurator<Function>::NeedsContext>,
    public StatisticHandler<Configurator<Function>::CollectStats>
{
  typedef typename WorkListTy::value_type value_type;
public:
  class UserAPI
    :public API_PerIter<Configurator<Function>::NeedsPIA>,
     public API_Push<Configurator<Function>::NeedsPush, WorkListTy>,
     public API_Pause<Configurator<Function>::NeedsPause>
  {
    friend class ParallelThreadContext;
  };

private:

  UserAPI facing;
  TerminationDetection::tokenHolder* lterm;
  bool leader;

public:
  ParallelThreadContext() {}
  
  virtual ~ParallelThreadContext() {}

  void initialize(TerminationDetection::tokenHolder* t,
		  bool _leader,
		  WorkListTy* wl,
		  PauseImpl<Configurator<Function>::NeedsPause>* p) {
    lterm = t;
    leader = _leader;
    facing.init_wl(wl);
    facing.init_pause(p);
  }

  void workHappened() {
    lterm->workHappened();
  }

  bool is_leader() const {
    return leader;
  }

  UserAPI& userFacing() {
    return facing;
  }

  void resetAlloc() {
    facing.__resetAlloc();
  }

};

template<class WorkListTy, class Function>
class ForEachWork : public Galois::Executable {
  typedef typename WorkListTy::value_type value_type;
  typedef GaloisRuntime::WorkList::MP_SC_FIFO<value_type> AbortedListTy;
  typedef ParallelThreadContext<Function, WorkListTy> PCTy;
  

  WorkListTy global_wl;
  PauseImpl<Configurator<Function>::NeedsPause> pauser;
  Function& f;

  PerCPU<PCTy> tdata;
  TerminationDetection term;
  AbortedListTy aborted;
  volatile long abort_happened; //hit flag

  bool drainAborted() {
    bool retval = false;
    abort_happened = 0;
    std::pair<bool, value_type> p = aborted.pop();
    while(p.first) {
      retval = true;
      global_wl.push(p.second);
      p = aborted.pop();
    };
    return retval;
  }

  void doAborted(value_type val) {
    aborted.push(val);
    abort_happened = 1;
  }

  void doProcess(value_type val, PCTy& tld) {
    tld.inc_iterations();
    tld.start_iteration();
    try {
      f(val, tld.userFacing());
    } catch (int a) {
      tld.cancel_iteration();
      tld.inc_conflicts();
      doAborted(val);
      return;
    }
    tld.commit_iteration();
    tld.resetAlloc();
  }

public:
  template<typename IterTy>
  ForEachWork(IterTy b, IterTy e, Function& _f)
    :f(_f) {
    global_wl.fill_initial(b, e);
  }
  
  ~ForEachWork() {
    typename PCTy::stat_sum s;
    for (int i = 0; i < s.num(); ++i)
      s.add(tdata.get(i));
    s.done();
    
    for (int i = 1; i < s.num(); ++i)
      tdata.get(0).merge_stat(tdata.get(i));
    tdata.get(0).report_stat();
    assert(global_wl.empty());
  }

  virtual void operator()() {
    PCTy& tld = tdata.get();
    tld.initialize(term.getLocalTokenHolder(), 
		   tdata.myEffectiveID() == 0,
		   &global_wl,
		   &pauser);
    tld.start_parallel_region();

    do {
    std::pair<bool, value_type> p = global_wl.pop();
    if (p.first) {
      tld.workHappened();
      doProcess(p.second, tld);
      do {
	if (tld.is_leader() && abort_happened) {
	  drainAborted();
	}
	pauser.checkPause();
	p = global_wl.pop();
	if (p.first) {
	  doProcess(p.second, tld);
	} else {
	  break;
	}
      } while(true);
    }
    if (tld.is_leader() && drainAborted())
      continue;

    pauser.checkPause();

      term.localTermination();
    } while (!term.globalTermination());

    tld.end_parallel_region();
  }
};


template<class Function>
class ForAllWork : public Galois::Executable {
  PerCPU<long> tdata;
  Function& f;
  long start, end;
  int numThreads;

public:
  ForAllWork(int _start, int _end, Function& _f) : f(_f), start(_start), end(_end) {
    numThreads = GaloisRuntime::getSystemThreadPool().getActiveThreads();
    assert(numThreads > 0);
  }
  
  ~ForAllWork() { 
    std::vector<long> list;
    for (int i = 0; i < numThreads; ++i)
      list.push_back(tdata.get(i));
    summarizeList("TotalTime", &list[0], &list[list.size()]);
  }

  virtual void operator()() {
    Timer T;
    T.start();
    // Simple blocked assignment
    unsigned int id = tdata.myEffectiveID();
    long range = end - start;
    long block = range / numThreads;
    long base = start + id * block;
    long stop = base + block;
    for (long i = base; i < stop; i++) {
      f(i);
    }
    // Remainder (each thread executes at most one iteration)
    for (long i = start + numThreads * block + id; i < end; i += numThreads) {
      f(i);
    }
    T.stop();
    tdata.get() = T.get();
  }
};

template<typename WLTy, typename IterTy, typename Function>
void for_each_impl(IterTy b, IterTy e, Function f) {
#ifdef GALOIS_VTUNE
  __itt_resume();
#endif

  typedef typename WLTy::template retype<typename std::iterator_traits<IterTy>::value_type>::WL aWLTy;

  ForEachWork<aWLTy, Function> GW(b, e, f);
  ThreadPool& PTP = getSystemThreadPool();
  PTP.run(&GW);

#ifdef GALOIS_VTUNE
  __itt_pause();
#endif
}

template<class Function>
void for_all_parallel(long start, long end, Function& f) {
  ForAllWork<Function> GW(start, end, f);
  ThreadPool& PTP = getSystemThreadPool();
  PTP.run(&GW);
}
}

#endif
