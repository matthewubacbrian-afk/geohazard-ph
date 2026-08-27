import { readOfflineValue, saveOfflineValue } from '../src/services/offlineCache';

test('stores last-known hazard data locally', () => {
  saveOfflineValue('latest', [{ id: 'sample' }]);

  expect(readOfflineValue('latest')).toEqual([{ id: 'sample' }]);
});
