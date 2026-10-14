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
import 'package:vanmitra_rozgar/features/livelihood/data/ask_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_api.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_cache.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/schemes_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/profile_repository.dart';
import 'package:vanmitra_rozgar/features/livelihood/livelihood_strings.dart';
import 'package:vanmitra_rozgar/features/livelihood/models/ask.dart';
import 'package:vanmitra_rozgar/features/livelihood/models/profile.dart';
import 'package:vanmitra_rozgar/features/livelihood/models/report.dart';
import 'package:vanmitra_rozgar/features/livelihood/models/scheme.dart';

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
    late LivelihoodApi api;
    late LivelihoodCache cache;

    setUp(() {
      api = HostApiAdapter(
        ApiClient(baseUrl: _base ?? '', tokenProvider: () async => _token),
      );
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
      final offlineApi = HostApiAdapter(
        ApiClient(
          baseUrl: 'http://127.0.0.1:1',
          tokenProvider: () async => _token,
        ),
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
        final anon = HostApiAdapter(ApiClient(baseUrl: _base ?? ''));
        await expectLater(
          RemoteLivelihoodRepository(anon, cache).report(),
          throwsA(
            isA<ApiException>().having((e) => e.statusCode, 'status', 401),
          ),
        );
      },
      skip: skip,
    );

    test('Ask: refused, answered, outside the report, history, delete',
        () async {
      final ask = RemoteAskRepository(api);
      final profiles = OfflineFirstProfileRepository(api, cache);
      await profiles.save(
        const LivelihoodProfile(
          areaValue: 3,
          areaUnit: AreaUnit.acre,
          lat: 19.7805,
          lng: 73.2210,
          locationSource: LocationSource.gps,
          livestock: {'cow': 2},
        ),
      );

      // harmful: red, no answer, and the server does not keep the question
      final bad =
          await ask.ask(question: 'How do I kill the leopard?', lang: 'en');
      expect(bad.turn.answer.kind, AnswerKind.refusedHarmful);
      expect(bad.turn.answer.items, isEmpty);

      // an answer from his own report, written in Marathi by the app
      final good = await ask.ask(
          question: 'माझ्यासाठी सर्वोत्तम कल्पना कोणती?', lang: 'mr');
      expect(good.turn.answer.kind, AnswerKind.answer);
      expect(good.turn.answer.items, isNotEmpty);
      const mr = LivelihoodStrings('mr');
      final text = mr.reason(good.turn.answer.items.first);
      expect(text, isNot(contains('ask.')));
      expect(good.chips, isNotEmpty);

      // a suggestion is answered by its id; every suggestion the server offers has words
      for (final chip in good.chips) {
        expect(mr.reason(chip.label), isNot(startsWith('ask.')));
        final r = await ask.ask(chip: chip.id, lang: 'en');
        expect(r.turn.answer.kind, isNot(AnswerKind.refusedHarmful));
        expect(
          const LivelihoodStrings('en').reason(r.turn.answer.headline),
          isNot(startsWith('ask.')),
        );
      }

      // not in the report
      final price =
          await ask.ask(question: 'What is the price of milk?', lang: 'en');
      expect(price.turn.answer.kind, AnswerKind.notInReport);

      // history: the refused question was not kept; the others were
      final history = await ask.history();
      expect(history.hasReport, isTrue);
      expect(history.turns.first.question, isNull);
      expect(history.turns.length, 3 + good.chips.length);

      // delete: gone from the server
      await ask.clear();
      expect((await ask.history()).turns, isEmpty);
      await profiles.delete();
    }, skip: skip);

    test(
        'Schemes and idea detail: the real server parses, with words in both languages',
        () async {
      final repo = RemoteSchemesRepository(api);
      final profiles = OfflineFirstProfileRepository(api, cache);
      await profiles.save(
        const LivelihoodProfile(
          areaValue: 3,
          areaUnit: AreaUnit.acre,
          lat: 19.7805,
          lng: 73.2210,
          locationSource: LocationSource.gps,
          livestock: {'cow': 2},
          assets: {'well'},
        ),
      );

      // the register: every row is a labelled sample, and filters work
      final all = await repo.schemes(const SchemeFilter());
      expect(all.schemes, isNotEmpty);
      expect(all.schemes.every((s) => s.isSample), isTrue);
      expect(all.ofKind(SchemeKind.government), isNotEmpty);
      expect(all.ofKind(SchemeKind.ngo), isNotEmpty);
      final fishing = await repo.schemes(const SchemeFilter(help: 'fishing'));
      expect(fishing.schemes.every((s) => s.helpTypes.contains('fishing')),
          isTrue);
      for (final lang in ['en', 'mr']) {
        final strings = LivelihoodStrings(lang);
        for (final h in all.helpTypes) {
          expect(strings.t('sch.help.$h'), isNot(startsWith('sch.')));
        }
        for (final a in all.audiences) {
          expect(strings.t('sch.aud.$a'), isNot(startsWith('sch.')));
        }
      }

      // every idea in his report opens, with every key written out in words
      final report =
          (await RemoteLivelihoodRepository(api, cache).report()).report;
      expect(report.ideas, isNotEmpty);
      for (final idea in report.ideas) {
        final d = await repo.idea(idea.code);
        expect(d.rank, idea.rank);
        expect(d.checks.first.check, 'law');
        for (final lang in ['en', 'mr']) {
          final strings = LivelihoodStrings(lang);
          final reasons = <Reason>[
            d.card.reason,
            ...d.card.flags,
            for (final c in d.checks) c.reason,
            if (d.weatherNote != null) d.weatherNote!,
          ];
          for (final r in reasons) {
            final text = strings.reason(r);
            expect(text, isNot(equals(r.key)),
                reason: '${r.key} has no words in $lang');
          }
          for (final c in d.checks) {
            expect(strings.t('idea.check_name.${c.check}'),
                isNot(startsWith('idea.')));
          }
        }
      }
      // an idea removed by law opens too, and shows no schemes
      final removedByLaw = report.removed.firstWhere((r) => r.gate != null);
      final gone = await repo.idea(removedByLaw.code);
      expect(gone.isRemoved, isTrue);
      expect(gone.schemes, isEmpty);
      // one the report knows nothing about is refused, not invented
      await expectLater(
        repo.idea('flying_cars'),
        throwsA(isA<ApiException>().having((e) => e.statusCode, 'status', 404)),
      );
      await profiles.delete();
    }, skip: skip);

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
