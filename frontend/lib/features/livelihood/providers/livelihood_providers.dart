import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/livelihood_repository.dart';
import '../models/report.dart';

/// Swap this for the server repository in the intake slice; screens do not change.
final livelihoodRepositoryProvider = Provider<LivelihoodRepository>(
  (ref) => const SeedLivelihoodRepository(),
);

final reportProvider = FutureProvider<Report>(
  (ref) => ref.watch(livelihoodRepositoryProvider).latestReport(),
);

/// Which resources the Resources screen shows. null = all.
final resourceFilterProvider = StateProvider<UsefulLabel?>((ref) => null);
