using TacticalAI.Core;
using UnityEngine;

namespace TacticalAI.Agents
{
    /// <summary>Контролери, досліджені в статті (підрозд. 4.6).</summary>
    public enum ControllerType
    {
        Topsis,             // запропонований метод
        TopsisAdmissible,   // метод з обмеженням допустимості Attack за нульового запасу боєприпасів
        WeightedSum,        // та сама матриця, агрегація зваженою сумою (абляція)
        Random,             // рівноймовірний вибір стратегії
        Naive               // завжди Attack
    }

    /// <summary>
    /// Періодично (з інтервалом decisionInterval) обирає стратегію агента на основі його поточного стану.
    /// </summary>
    [RequireComponent(typeof(AgentSensor))]
    public class AgentBrain : MonoBehaviour
    {
        [SerializeField] private ControllerType controller = ControllerType.Topsis;
        [Tooltip("Ваги критеріїв S1…S6; сума нормується автоматично")]
        [SerializeField] private float[] weights = { 0.20f, 0.20f, 0.15f, 0.20f, 0.10f, 0.15f };
        [SerializeField] private float decisionInterval = 0.1f;

        private AgentSensor sensor;
        private TacticalDecisionMaker decisionMaker;
        private float timer;

        public Strategy CurrentStrategy { get; private set; } = Strategy.Attack;
        public CombatAgent NearestEnemy { get; private set; }
        public AgentState LastState { get; private set; }
        public double[] LastScores { get; private set; } = new double[3];

        private void Awake()
        {
            sensor = GetComponent<AgentSensor>();
            var w = new double[weights.Length];
            for (int j = 0; j < w.Length; j++) w[j] = weights[j];
            decisionMaker = new TacticalDecisionMaker(
                w,
                controller == ControllerType.TopsisAdmissible,
                controller == ControllerType.WeightedSum ? Aggregation.WeightedSum : Aggregation.Topsis);
        }

        private void Update()
        {
            timer -= Time.deltaTime;
            if (timer > 0f) return;
            timer = decisionInterval;
            Decide();
        }

        public void Decide()
        {
            LastState = sensor.ReadState(out CombatAgent enemy);
            NearestEnemy = enemy;
            switch (controller)
            {
                case ControllerType.Naive:
                    CurrentStrategy = Strategy.Attack;
                    break;
                case ControllerType.Random:
                    CurrentStrategy = (Strategy)Random.Range(0, 3);
                    break;
                default:
                    CurrentStrategy = decisionMaker.Decide(LastState, out double[] c);
                    LastScores = c;
                    break;
            }
        }
    }
}
