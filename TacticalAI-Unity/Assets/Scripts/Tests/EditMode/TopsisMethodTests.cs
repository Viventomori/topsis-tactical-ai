using NUnit.Framework;
using TacticalAI.Core;

namespace TacticalAI.Tests
{
    /// <summary>
    /// Перевірка C#-реалізації на числах зі статті (підрозд. 2.3, табл. 4, 7, 8; підрозд. 4.5–4.6).
    /// Ті самі значення дає simulation/example_topsis.py.
    /// Запуск: Window → General → Test Runner → EditMode → Run All.
    /// </summary>
    public class TopsisMethodTests
    {
        private const double Tol = 1e-4;

        [Test]
        public void ThreatLevel_MatchesFormula4()
        {
            Assert.AreEqual(5.0, AgentState.ThreatLevel(2, 3), 1e-6);
            Assert.AreEqual(0.0, AgentState.ThreatLevel(4, 0), 1e-6);
        }

        [Test]
        public void DecisionMatrix_MatchesTable4()
        {
            double[][] x = StrategyEvaluator.BuildDecisionMatrix(new AgentState(20, 60, 2, 3, true));
            double[][] expected =
            {
                new[] { 6.6667, 7.5, 6.6667, 2.5, 6.0, 5.0 },
                new[] { 2.8, 8.0, 7.0, 6.0, 10.0, 3.5 },
                new[] { 0.0, 0.0, 2.6667, 5.0, 3.0, 5.0 }
            };
            for (int i = 0; i < 3; i++)
                for (int j = 0; j < 6; j++)
                    Assert.AreEqual(expected[i][j], x[i][j], Tol, $"x[{i}][{j}]");
        }

        [Test]
        public void Closeness_MatchesTable7_AndAttackIsChosen()
        {
            var dm = new TacticalDecisionMaker();
            Strategy s = dm.Decide(new AgentState(20, 60, 2, 3, true), out double[] c);
            Assert.AreEqual(0.7227, c[0], Tol);
            Assert.AreEqual(0.6497, c[1], Tol);
            Assert.AreEqual(0.2108, c[2], Tol);
            Assert.AreEqual(Strategy.Attack, s);
        }

        [TestCase(0, Strategy.Attack)]
        [TestCase(3, Strategy.Attack)]
        [TestCase(4, Strategy.Defense)]
        [TestCase(7, Strategy.Defense)]
        public void Sensitivity_MatchesTable8(int enemies, Strategy expected)
        {
            var dm = new TacticalDecisionMaker();
            Assert.AreEqual(expected, dm.Decide(new AgentState(20, 60, 2, enemies, true)));
        }

        [Test]
        public void LowResources_RetreatIsChosen()
        {
            var dm = new TacticalDecisionMaker();
            Strategy s = dm.Decide(new AgentState(5, 30, 0, 3, false), out double[] c);
            Assert.AreEqual(Strategy.Retreat, s);
            Assert.AreEqual(0.614, c[2], 1e-3);
        }

        [Test]
        public void Compensation_AttackWithoutAmmo_AndAdmissibilityConstraint()
        {
            var state = new AgentState(0, 70, 1, 0, false);
            var plain = new TacticalDecisionMaker();
            Assert.AreEqual(Strategy.Attack, plain.Decide(state, out double[] c));   // компенсаційний ефект (підрозд. 4.5)
            Assert.AreEqual(0.584, c[0], 1e-3);
            Assert.AreEqual(0.419, c[2], 1e-3);

            var constrained = new TacticalDecisionMaker(enforceAdmissibility: true); // обмеження допустимості (підрозд. 4.6)
            Strategy s = constrained.Decide(state, out double[] c2);
            Assert.AreNotEqual(Strategy.Attack, s);
            Assert.IsTrue(double.IsNaN(c2[0]));
        }

        [Test]
        public void ArgMax_TieBreaksToFirstStrategy()
        {
            Assert.AreEqual(0, TopsisSolver.ArgMax(new[] { 0.5, 0.5, 0.1 }));
        }
    }
}
