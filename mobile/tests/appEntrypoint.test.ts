jest.mock('react-native', () => ({
  AppRegistry: { registerComponent: jest.fn() },
}));

jest.mock('../src/App', () => ({ __esModule: true, default: 'GeoHazardApp' }));

describe('mobile app entrypoint', () => {
  it('uses a valid registered component name and preserves the display label', () => {
    const appConfig = require('../app.json');

    expect(appConfig.name).toBe('GeoHazardPH');
    expect(appConfig.displayName).toBe('GeoHazard PH');
  });

  it('registers the existing app component with AppRegistry', () => {
    const { AppRegistry } = require('react-native');
    const { default: App } = require('../src/App');
    const appConfig = require('../app.json');

    require('../index.js');

    expect(AppRegistry.registerComponent).toHaveBeenCalledWith(
      appConfig.name,
      expect.any(Function),
    );
    expect(AppRegistry.registerComponent.mock.calls[0][1]()).toBe(App);
  });
});
