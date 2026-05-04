// Ablation 2 on the safe chain: sigma_obs is treated as known (data,
// not parameter). Justified when the standard candle's intrinsic
// scatter and the distance-modulus measurement noise have been
// calibrated externally. Builds on additive (q0 retained, since
// dropping q0 fails safety).

data {
  int<lower=1> N;
  vector[N] z_obs;
  vector[N] mu_obs;
  real<lower=0> d_min;
  real<lower=d_min> d_max;
  real q0;
  real<lower=0> sigma_obs;     // data
}

transformed data {
  real c_kms = 299792.458;
}

parameters {
  real<lower=0> H0;
  real<lower=0> sigma_v;
  vector<lower=d_min, upper=d_max>[N] d;
}

transformed parameters {
  vector[N] z_cos = H0 * d / c_kms;
  vector[N] v_implied = c_kms * (z_obs - z_cos);
  vector[N] d_L = d .* (1 + 0.5 * (1 - q0) * z_cos);
  vector[N] mu_pred = 5 * log10(d_L) + 25;
}

model {
  H0 ~ normal(70, 30);
  sigma_v ~ normal(0, 500);

  target += 2 * sum(log(d));

  v_implied ~ normal(0, sigma_v);

  mu_obs ~ normal(mu_pred, sigma_obs);
}
