# data/stability

`qk_norm_test.json`: BOM-27's check that QK-norm prevents high-learning-rate instability before
training the 590M mid model (Amendment 39). Four runs of the 125M shape for 1,500 steps on three
training token files, at 10x and 30x the registered peak learning rate, with and without QK-norm
(`timelocked_lm.train pilot --max-steps 1500 --lr-scale N [--qk-norm]`) on a rented 2 x H100;
per-window median loss and gradient norm and the final validation loss. Numbers only.
