from rescue_rag.sec.client import RateLimiter


def test_rate_limiter_spaces_calls():
    t = [0.0]
    slept = []

    def sleep(d):
        slept.append(d)
        t[0] += d

    rl = RateLimiter(4, clock=lambda: t[0], sleep=sleep)
    for _ in range(3):
        rl.wait()
    assert slept == [0.25, 0.25]
