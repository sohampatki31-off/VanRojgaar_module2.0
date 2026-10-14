import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/livelihood/data/livelihood_cache.dart';
import 'shell/shell_app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // LIVE mode keeps his details and last report in an encrypted box on the phone; the demo
  // keeps nothing (see shell_app.dart).
  final overrides = shellIsLive
      ? liveOverrides(await HiveCacheStore.open())
      : <Override>[];
  runApp(ProviderScope(overrides: overrides, child: const ShellApp()));
}
