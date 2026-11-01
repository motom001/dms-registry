// Single-threaded stand-ins for <mutex>/<thread> on WASI without threads (wasi-sdk libc++ has none).
// Tesseract only uses them for locking and an optional background prefetch; here everything runs inline.
#pragma once
#ifdef __cplusplus
#include <__config>
#include <utility>
#include <chrono>
#include <functional>
namespace std {
struct mutex { void lock() {} void unlock() {} bool try_lock() { return true; } };
struct thread {
  thread() = default;
  template <class F, class... A> explicit thread(F &&f, A &&...a) { std::invoke(std::forward<F>(f), std::forward<A>(a)...); }
  bool joinable() const { return false; }
  void join() {}
  void detach() {}
};
namespace this_thread {
template <class R, class P> void sleep_for(const chrono::duration<R, P> &) {}
inline void yield() {}
}
}
#endif
