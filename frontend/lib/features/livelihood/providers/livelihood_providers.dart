import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/livelihood_repository.dart';
import '../models/report.dart';

/// The shell (or the host) overrides this with the server repository once a login exists. The
/// default is the bundled SAMPLE report, so the feature always runs.
final livelihoodRepositoryProvider = Provider<LivelihoodRepository>(
  (ref) => const SeedLivelihoodRepository(),
);

/// His report: built on the server when it can be, otherwise the last one saved on the phone.
/// Invalidate it after his details change, so the next look builds a fresh one.
final reportProvider = FutureProvider<ReportResult>(
  (ref) => ref.watch(livelihoodRepositoryProvider).report(),
);

/// Which resources the Resources screen shows. null = all.
final resourceFilterProvider = StateProvider<UsefulLabel?>((ref) => null);
