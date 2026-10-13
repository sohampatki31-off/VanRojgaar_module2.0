import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../livelihood_routes.dart';
import '../livelihood_strings.dart';
import '../providers/livelihood_providers.dart';
import '../widgets/lv_badges.dart';
import '../widgets/lv_scaffold.dart';
import '../widgets/report_parts.dart';

/// Entry screen. In this slice it opens the bundled report; the next slice adds the intake form
/// ("Add your details") in front of it.
class LivelihoodHomeScreen extends ConsumerWidget {
  const LivelihoodHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = LivelihoodStrings.of(context);
    final c = context.colors;
    final report = ref.watch(reportProvider);

    return LvScaffold(
      title: s.t('lv_card_title'),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: c.cardBg,
              borderRadius: BorderRadius.circular(AppRadius.lg),
              border: Border.all(color: c.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.agriculture_rounded,
                  size: 40,
                  color: AppColors.forestSage,
                ),
                const SizedBox(height: AppSpacing.md),
                Text(
                  s.t('lv_title'),
                  style: AppTypography.display.copyWith(color: c.textPrimary),
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  s.t('lv_home_intro'),
                  style: AppTypography.bodyLarge.copyWith(
                    color: c.textSecondary,
                  ),
                ),
                report.maybeWhen(
                  data: (r) => r.isSampleData
                      ? Padding(
                          padding: const EdgeInsets.only(top: AppSpacing.md),
                          child: Wrap(
                            spacing: AppSpacing.sm,
                            children: [const SampleChip()],
                          ),
                        )
                      : const SizedBox.shrink(),
                  orElse: () => const SizedBox.shrink(),
                ),
                report.maybeWhen(
                  data: (r) => r.isSampleData
                      ? NoteLine(
                          s.t('lv_sample_note'),
                          icon: Icons.science_outlined,
                        )
                      : const SizedBox.shrink(),
                  orElse: () => const SizedBox.shrink(),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          FilledButton.icon(
            onPressed: () =>
                Navigator.of(context).pushNamed(LivelihoodRoutes.report),
            icon: const Icon(Icons.assessment_rounded),
            label: Text(
              s.t('lv_show_report'),
              style: AppTypography.labelLarge.copyWith(
                color: Colors.white,
                fontSize: 16,
              ),
            ),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.saffron,
              foregroundColor: Colors.white,
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
            ),
          ),
          const SuggestionFooter(),
        ],
      ),
    );
  }
}
