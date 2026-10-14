import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/theme/app_colors.dart';
import '../features/livelihood/data/livelihood_repository.dart';
import '../features/livelihood/data/profile_repository.dart';
import '../features/livelihood/livelihood_routes.dart';
import '../features/livelihood/providers/host_hooks.dart';
import '../features/livelihood/providers/livelihood_providers.dart';
import '../features/livelihood/providers/profile_providers.dart';

// THROWAWAY SHELL. It exists only so the feature can run on its own: a theme, a language and a
// theme switch, the routes, and the wiring of the repositories. It is deleted at merge; the host
// app supplies all of this (docs/INTEGRATION.md). Nothing under lib/features/livelihood/ imports
// from here.
//
// Two ways to run it:
//   * LIVE: `flutter run --dart-define=VANMITRA_API_BASE_URL=http://10.0.2.2:8010
//           --dart-define=VANMITRA_DEV_TOKEN=<token from backend/scripts/dev_token.py>`
//     The feature's DEFAULT wiring: talks to the backend, and keeps his details and last report
//     on the phone (encrypted). This is exactly how it behaves inside the host app.
//   * DEMO (no server): `flutter run` with no address. The shell swaps in the bundled SAMPLE
//     report and keeps his details in memory.

const _apiBaseUrl = String.fromEnvironment('VANMITRA_API_BASE_URL');

/// True when a server address was supplied.
bool get shellIsLive => _apiBaseUrl.isNotEmpty;

/// The overrides for the DEMO (no server). Live mode needs none: it is the feature's default.
List<Override> demoOverrides() => shellIsLive
    ? const []
    : [
        livelihoodRepositoryProvider
            .overrideWithValue(const SeedLivelihoodRepository()),
        profileRepositoryProvider.overrideWithValue(MemoryProfileRepository()),
      ];

final _localeProvider = StateProvider<Locale>(
  (ref) => const Locale('mr'),
); // host default: Marathi
final _themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.light);

ThemeData _theme(Brightness b) {
  final dark = b == Brightness.dark;
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.forestCanopy,
    brightness: b,
  ).copyWith(
    primary: dark ? AppColors.forestMist : AppColors.forestCanopy,
    secondary: AppColors.saffron,
    surface: dark ? AppColors.darkCard : AppColors.surfaceCard,
    error: AppColors.alertRed,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    fontFamily: 'NotoSansDevanagari',
    scaffoldBackgroundColor:
        dark ? AppColors.darkSurface : AppColors.surfaceBase,
  );
}

class ShellApp extends ConsumerWidget {
  const ShellApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(_localeProvider);
    return ProviderScope(
      overrides: [
        hostAppBarActionsProvider.overrideWithValue(const [
          _LanguageButton(),
          _ThemeButton(),
        ]),
      ],
      child: MaterialApp(
        title: 'VanMitra Module 4',
        debugShowCheckedModeBanner: false,
        theme: _theme(Brightness.light),
        darkTheme: _theme(Brightness.dark),
        themeMode: ref.watch(_themeModeProvider),
        locale: locale,
        supportedLocales: const [Locale('en'), Locale('hi'), Locale('mr')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        initialRoute: LivelihoodRoutes.home,
        routes: livelihoodRoutes,
      ),
    );
  }
}

class _LanguageButton extends ConsumerWidget {
  const _LanguageButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mr = ref.watch(_localeProvider).languageCode == 'mr';
    return TextButton(
      style: TextButton.styleFrom(
        foregroundColor: Colors.white,
        minimumSize: const Size(48, 48),
      ),
      onPressed: () =>
          ref.read(_localeProvider.notifier).state = Locale(mr ? 'en' : 'mr'),
      child: Text(mr ? 'EN' : 'मराठी'),
    );
  }
}

class _ThemeButton extends ConsumerWidget {
  const _ThemeButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dark = ref.watch(_themeModeProvider) == ThemeMode.dark;
    return IconButton(
      tooltip: dark ? 'Light theme' : 'Dark theme',
      color: Colors.white,
      constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
      icon: Icon(dark ? Icons.light_mode_rounded : Icons.dark_mode_rounded),
      onPressed: () => ref.read(_themeModeProvider.notifier).state =
          dark ? ThemeMode.light : ThemeMode.dark,
    );
  }
}
