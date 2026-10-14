// LIVE contract test: the real ApiClient and repositories against a RUNNING backend.
// It is skipped unless VANMITRA_LIVE_API is set, so `flutter test` stays offline by default.
//
//   cd backend && set VANMITRA_LIVELIHOOD_DEV_USERS=true && python -m uvicorn app.main:app --port 8011
//   set VANMITRA_LIVE_API=http://127.0.0.1:8011
//   set VANMITRA_LIVE_TOKEN=<output of python scripts/dev_token.py>
//   flutter test test/live_contract_test.dart
//
// The server must be a fresh in-memory one (the test saves, reads and deletes the demo user's
// profile). It proves the Dart models parse what the server really sends, in Marathi too.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:vanmitra_rozgar/core/api/api_client.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_cache.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/profile_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/models/profile.dart';

final _base = Platform.environment['VANMITRA_LIVE_API'];
final _token = Platform.environment['VANMITRA_LIVE_TOKEN'];

void main() {
  final skip = (_base == null || _token == null)
      ? 'set VANMITRA_LIVE_API and VANMITRA_LIVE_TOKEN to run against a live backend'
      : false;

  setUpAll(
    () => HttpOverrides.global = null,
  ); // flutter_test blocks real HTTP by default

  group('live backend', () {
    late ApiClient api;
    late LivelihoodCache cache;

    setUp(() {
      api = ApiClient(baseUrl: _base ?? '', tokenProvider: () async => _token);
      cache = LivelihoodCache(MemoryCacheStore());
    });

    test('the whole journey: save, report, offline fallback, delete', () async {
      final profiles = OfflineFirstProfileRepository(api, cache);

      // a fresh server has nothing saved
      expect(await profiles.load(), isNull);

      // save his details (this is exactly what the intake form sends)
      const mine = LivelihoodProfile(
        areaValue: 3,
        areaUnit: AreaUnit.acre,
        landType: LandType.irrigated,
        waterOnLand: WaterOnLand.openWell,
        lat: 19.7805,
        lng: 73.2210,
        accuracyM: 8,
        locationSource: LocationSource.gps,
        livestock: {'cow': 2, 'goat_sheep': 5},
        assets: {'well', 'pump', 'shed'},
        pastWork: {'dairy', 'millets'},
        familyWorkers: 3,
        moneyLevel: MoneyLevel.medium,
      );
      await profiles.save(mine);
      expect(profiles.pendingSync, isFalse);

      // a second phone (empty cache) sees the same details from the server
      final other = await OfflineFirstProfileRepository(
        api,
        LivelihoodCache(MemoryCacheStore()),
      ).load();
      expect(other!.areaHa, closeTo(1.214, 1e-3));
      expect(other.livestock, {'cow': 2, 'goat_sheep': 5});
      expect(other.assets, {'pump', 'shed', 'well'});
      expect(other.locationSource, LocationSource.gps);

      // build his report: the Dart models must read what the server really sends
      final reports = RemoteLivelihoodRepository(api, cache);
      final live = await reports.report();
      expect(live.fromCache, isFalse);
      final r = live.report;
      expect(r.header.level, 'plot');
      expect(r.header.name, 'Demo villager');
      expect(r.header.radiusM, 5000);
      expect(r.isSampleData, isTrue);
      expect(r.resources, hasLength(10));
      expect(
        r.resources.map((x) => x.distanceM),
        orderedEquals([...r.resources.map((x) => x.distanceM)]..sort()),
      );
      expect(r.resources.first.nameMr, isNotEmpty);
      expect(r.resources.every((x) => x.trust.source.isNotEmpty), isTrue);
      expect(r.ideas.length, lessThanOrEqualTo(5));
      expect(r.ideas.take(3).map((i) => i.code), contains('dairy_small'));
      expect(r.analysis.headline.key, startsWith('analysis.headline.'));
      expect(r.weather, isNotNull);

      // the server dropped the network: the same report comes back from the phone
      final offlineApi = ApiClient(
        baseUrl: 'http://127.0.0.1:1',
        tokenProvider: () async => _token,
        timeout: const Duration(seconds: 3),
      );
      final offline = await RemoteLivelihoodRepository(
        offlineApi,
        cache,
      ).report();
      expect(offline.fromCache, isTrue);
      expect(offline.report.id, r.id);

      // delete his answers: the details AND the reports made from them are gone
      await profiles.delete();
      expect(profiles.pendingSync, isFalse);
      expect(
        await OfflineFirstProfileRepository(
          api,
          LivelihoodCache(MemoryCacheStore()),
        ).load(),
        isNull,
      );
      await expectLater(
        api.get('/livelihood/report/latest'),
        throwsA(
          isA<ApiException>().having(
            (e) => e.messageKey,
            'key',
            'livelihood.no_report',
          ),
        ),
      );
    }, skip: skip);

    test(
      'without a login the server refuses, and we say so in plain terms',
      () async {
        final anon = ApiClient(baseUrl: _base ?? '');
        await expectLater(
          RemoteLivelihoodRepository(anon, cache).report(),
          throwsA(
            isA<ApiException>().having((e) => e.statusCode, 'status', 401),
          ),
        );
      },
      skip: skip,
    );

    test('a place outside Maharashtra is refused by the server', () async {
      final profiles = OfflineFirstProfileRepository(api, cache);
      await expectLater(
        profiles.save(
          const LivelihoodProfile(
            lat: 28.6,
            lng: 77.2,
            locationSource: LocationSource.manual,
          ),
        ),
        throwsA(
          isA<ApiException>().having(
            (e) => e.messageKey,
            'key',
            'livelihood.location_outside_maharashtra',
          ),
        ),
      );
      expect(await profiles.load(), isNull); // and nothing was kept
    }, skip: skip);
  });
}
