import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;

import '../models/report.dart';

/// The one door the screens use to get a report (PDF §16), so no screen knows where data comes
/// from. Slice F1 has the bundled-file implementation; the server implementation arrives with
/// the intake form, when there is something to send.
abstract class LivelihoodRepository {
  Future<Report> latestReport();
}

/// Reads the bundled report, which was built by the backend from SAMPLE (synthetic) data.
/// This is also the fallback if the server is not reachable (docs/MVP_SPRINT.md §3).
class SeedLivelihoodRepository implements LivelihoodRepository {
  const SeedLivelihoodRepository({
    this.assetPath = 'assets/livelihood/sample_report.json',
  });

  final String assetPath;

  @override
  Future<Report> latestReport() async {
    final raw = await rootBundle.loadString(assetPath);
    return Report.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }
}
