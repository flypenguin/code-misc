#!/usr/bin/env bash

# create a session, start the first worker in it.
tmux new-session -s celery-workers -n main -d \
     celery -A workers.rule_based worker -n rulez -Q qc-quick

# split the pane down, this will be pane "1" (the "old" one is pane "0")
# start the 2nd worker in it
tmux split-window -t 0 -v -l 66% \
     celery -A workers.predict_deviation worker -n prediction -Q qc-quick

# split the NEWER pane ("1") down, now 50% size (cause the pane is 66%
# of all window space, and HALF of that is 33% of ALL window space, but
# still 50% of THE LOWER PANE)
# start the 3rd worker in it
tmux split-window -t 1 -v -l 50% \
     celery -A workers.train_deviation worker -n training -Q ml-train

# make sure all key presses (CTRL-C) go to all panes :)))
# "set-option -w" sets a window option
tmux set-option -w -t main synchronize-panes on

# now attach :D
tmux attach
