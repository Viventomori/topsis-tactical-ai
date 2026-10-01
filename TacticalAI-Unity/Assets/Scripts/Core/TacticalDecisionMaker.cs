using System.Collections.Generic;

namespace TacticalAI.Core
{
    /// <summary>Спосіб агрегації оцінок придатності.</summary>
    public enum Aggregation
    {
        Topsis,
        WeightedSum
    }

    /// <summary>
    /// Метод вибору тактичної стратегії: стан агента → матриця рішень (табл. 2) → ранжування → i* = arg max C_i (9).
    /// Опційно застосовується некомпенсаторне обмеження допустимості: за s_i1 = 0 стратегія Attack вилучається
    /// з множини альтернатив до побудови матриці рішень (підрозд. 4.6 статті).
    /// </summary>
    public sealed class TacticalDecisionMaker
    {
        /// <summary>Базові ваги критеріїв w = (0,20; 0,20; 0,15; 0,20; 0,10; 0,15) (підрозд. 2.3).</summary>
        public static readonly double[] DefaultWeights = { 0.20, 0.20, 0.15, 0.20, 0.10, 0.15 };

        public double[] Weights { get; }
        public bool EnforceAdmissibility { get; }
        public Aggregation Aggregation { get; }

        public TacticalDecisionMaker(double[] weights = null, bool enforceAdmissibility = false, Aggregation aggregation = Aggregation.Topsis)
        {
            Weights = (double[])(weights ?? DefaultWeights).Clone();
            EnforceAdmissibility = enforceAdmissibility;
            Aggregation = aggregation;
        }

        /// <summary>Обирає стратегію; closeness — оцінки для кожної стратегії (NaN для недопустимих).</summary>
        public Strategy Decide(AgentState state, out double[] closeness)
        {
            double[][] full = StrategyEvaluator.BuildDecisionMatrix(state);

            var admissible = new List<int>(StrategyEvaluator.StrategyCount);
            for (int i = 0; i < StrategyEvaluator.StrategyCount; i++)
            {
                if (EnforceAdmissibility && i == (int)Strategy.Attack && state.Ammo <= 0) continue;
                admissible.Add(i);
            }

            var sub = new double[admissible.Count][];
            for (int k = 0; k < admissible.Count; k++) sub[k] = full[admissible[k]];

            double[] c = Aggregation == Aggregation.Topsis
                ? TopsisSolver.Solve(sub, Weights)
                : TopsisSolver.WeightedSum(sub, Weights);

            closeness = new double[StrategyEvaluator.StrategyCount];
            for (int i = 0; i < closeness.Length; i++) closeness[i] = double.NaN;
            for (int k = 0; k < admissible.Count; k++) closeness[admissible[k]] = c[k];

            return (Strategy)admissible[TopsisSolver.ArgMax(c)];
        }

        public Strategy Decide(AgentState state)
        {
            return Decide(state, out _);
        }
    }
}
