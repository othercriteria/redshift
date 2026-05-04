// The punchline: the leanest safe model (additive + fixed sigma_obs)
// with the distance-modulus likelihood dropped entirely. Without an
// independent distance proxy, the only data is z_obs[1:N]; the model
// can only constrain (H0, sigma_v) through the volume prior on d, the
// peculiar-velocity prior, and the shape of the observed redshift
// distribution. The (H0, sigma_v) joint should noticeably broaden, and
// any visible degeneracy ridge is the headline of this section.

data {
  int<lower=1> N;
  vector[N] z_obs;
  real<lower=0> d_min;
  real<lower=d_min> d_max;
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
}

model {
  H0 ~ normal(70, 30);
  sigma_v ~ normal(0, 500);

  target += 2 * sum(log(d));

  v_implied ~ normal(0, sigma_v);
}
