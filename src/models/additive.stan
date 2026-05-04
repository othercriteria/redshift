// Ablation 1: additive redshift combination, z_obs ≈ z_cos + z_pec.
//
// This drops the (1+z)(1+z) cross term that the complete model carries.
// At z ≲ 0.1 the cross term contributes z^2 ~ 0.01, well below the
// per-galaxy noise budget. The Jacobian dz_obs/dv = 1/c becomes a
// constant, so it falls out of the likelihood entirely (constant log
// terms are dropped). All other modelling choices match complete.stan.

data {
  int<lower=1> N;
  vector[N] z_obs;
  vector[N] mu_obs;
  real<lower=0> d_min;
  real<lower=d_min> d_max;
  real q0;
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
  vector[N] d_L = d .* (1 + 0.5 * (1 - q0) * z_cos);
  vector[N] mu_pred = 5 * log10(d_L) + 25;
}

model {
  H0 ~ normal(70, 30);
  sigma_v ~ normal(0, 500);
  sigma_obs ~ normal(0, 0.3);

  target += 2 * sum(log(d));   // volume prior

  v_implied ~ normal(0, sigma_v);  // additive: no Jacobian

  mu_obs ~ normal(mu_pred, sigma_obs);
}
