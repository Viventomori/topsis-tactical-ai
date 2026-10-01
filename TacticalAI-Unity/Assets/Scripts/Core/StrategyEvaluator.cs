namespace TacticalAI.Core
{
    /// <summary>
    /// Побудова матриці рішень X = [x_ij] (m = 3 стратегії × n = 6 критеріїв) за функціями придатності табл. 2.
    /// Усі оцінки мають шкалу 0…10; більше значення — вища доречність стратегії за критерієм.
    /// Еквівалент функції build_matrix() у simulation/battle_sim.py (matrix_v1).
    /// </summary>
    public static class StrategyEvaluator
    {
        public const int StrategyCount = 3;
        public const int CriteriaCount = 6;

        /// <summary>φ(v) = max(0, min(1, v)).</summary>
        public static double Phi(double v)
        {
            return v < 0 ? 0 : v > 1 ? 1 : v;
        }

        public static double[][] BuildDecisionMatrix(AgentState s)
        {
            double ammo = s.Ammo, hp = s.Hp, allies = s.Allies, enemies = s.Enemies, threat = s.Threat;
            bool cover = s.InCover;

            double[] attack =
            {
                10 * Phi(ammo / 30),          // S1
                10 * Phi(hp / 80),            // S2
                10 * Phi(allies / 3),         // S3
                10 * Phi(1 - enemies / 4),    // S4
                cover ? 6 : 4,                // S5 = 4 + 2·s_i5
                10 * Phi(1 - threat / 10)     // S6
            };
            double[] defense =
            {
                4.2 * Phi(ammo / 30),         // S1 (тотожно 7·φ(ammo/50) за ammo ≤ 30)
                8 * Phi(hp / 50),             // S2
                7 * Phi(allies / 2),          // S3
                8 * Phi(enemies / 4),         // S4
                cover ? 10 : 3,               // S5 = 3 + 7·s_i5
                7 * Phi(threat / 10)          // S6
            };
            double[] retreat =
            {
                10 * Phi(1 - ammo / 15),      // S1
                10 * Phi(1 - hp / 30),        // S2
                8 * Phi(1 - allies / 3),      // S3
                10 * Phi(enemies / 6),        // S4
                cover ? 3 : 7,                // S5 = 7 − 4·s_i5
                10 * Phi(threat / 10)         // S6
            };
            return new[] { attack, defense, retreat };
        }
    }
}
