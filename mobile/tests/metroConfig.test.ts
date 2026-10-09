describe('Metro configuration', () => {
  it('loads the React Native Metro config for the native app', () => {
    const config = require('../metro.config');

    expect(config.resolver).toBeDefined();
    expect(config.transformer).toBeDefined();
  });
});
