# 2 Positive Short Bot

This automated trading bot trades LQTYUSDT on the Binance exchange.
Start a trade if the applicable conditions below are met.

--

1. Take the average of the volume over 3600 1-minute candles and double it as a threshold.
2. If there are 2 consecutive positive candles above the threshold, we will enter a short position 7 minutes after the signal.
3. 55 minutes after entering the short position, go long and close the position.
