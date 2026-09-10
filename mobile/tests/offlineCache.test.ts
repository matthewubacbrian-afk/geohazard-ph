import { readOfflineValue, saveOfflineValue } from '../src/services/offlineCache';

describe('offline cache', () => {
  it('stores last-known hazard data locally', () => {
  saveOfflineValue('latest', [{ id: 'sample' }]);

  expect(readOfflineValue('latest')).toEqual([{ id: 'sample' }]);
});

});
