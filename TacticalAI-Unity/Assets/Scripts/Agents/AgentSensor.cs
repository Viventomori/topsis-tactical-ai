using TacticalAI.Core;
using UnityEngine;

namespace TacticalAI.Agents
{
    /// <summary>
    /// Визначає множини Allies_i(τ) і Enemies_i(τ) у межах радіуса виявлення R_sense (формули (1), (2))
    /// і формує вектор стану агента s_i(τ).
    /// </summary>
    [RequireComponent(typeof(CombatAgent))]
    public class AgentSensor : MonoBehaviour
    {
        [SerializeField] private float senseRadius = 30f;

        private CombatAgent self;

        public float SenseRadius => senseRadius;

        private void Awake() { self = GetComponent<CombatAgent>(); }

        public AgentState ReadState(out CombatAgent nearestEnemy)
        {
            int allies = 0, enemies = 0;
            nearestEnemy = null;
            float nearest = float.MaxValue;
            Vector3 p = transform.position;

            foreach (CombatAgent other in CombatAgent.All)
            {
                if (other == self || !other.IsAlive) continue;
                float d = Vector3.Distance(p, other.transform.position);
                if (d > senseRadius) continue;
                if (other.Team == self.Team)
                {
                    allies++;
                }
                else
                {
                    enemies++;
                    if (d < nearest) { nearest = d; nearestEnemy = other; }
                }
            }
            return new AgentState(self.Ammo, self.Hp, allies, enemies, self.InCover);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, 0.8f, 0f, 0.4f);
            Gizmos.DrawWireSphere(transform.position, senseRadius);
        }
    }
}
