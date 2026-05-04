// COUNTER-EXAMPLE — this ablation fails the safety check.
//
// On top of the additive simplification, treats the proper distance as
// the luminosity distance (drops the q0 correction). The d_L/d shift is
// only ~8% at z=0.1 and *looks* small relative to sigma_obs ≈ 0.11 mag,
// but it gets fully absorbed into H0: in our recovery test the
// posterior median H0 drifts to 67.76 against a truth of 70 (~13σ on
// the credible interval), and sigma_v doubles to compensate.
//
// We keep this model in the repo specifically to show, in the
// deliverable, that "looks small" is not the same as "safe to drop".
// The leanest safe ablation chain stops at additive with q0 retained.

data {
  int<lower=1> N;
  vector[N] z_obs;
  vector[N] mu_obs;
  real<lower=0> d_min;
  real<lower=d_min> d_max;
}

transformed data {
  real c_kms = 299792.458;
}

parameters {
  real<lower=0> H0;
  real<lower=0> sigma_v;
  real<lower=0> sigma_obs;
  vector<lower=d_min, upper=d_max>[N] d;
}

transformed parameters {
  vector[N] z_cos = H0 * d / c_kms;
  vector[N] v_implied = c_kms * (z_obs - z_cos);
  vector[N] mu_pred = 5 * log10(d) + 25;  // d_L = d
}

model {
  H0 ~ normal(70, 30);
  sigma_v ~ normal(0, 500);
  sigma_obs ~ normal(0, 0.3);

  target += 2 * sum(log(d));   // volume prior

  v_implied ~ normal(0, sigma_v);

  mu_obs ~ normal(mu_pred, sigma_obs);
}
