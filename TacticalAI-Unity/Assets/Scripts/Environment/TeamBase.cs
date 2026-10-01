using System.Collections.Generic;
using TacticalAI.Agents;
using TacticalAI.Core;
using UnityEngine;

namespace TacticalAI.Environment
{
    /// <summary>
    /// База команди: агент своєї команди зі стратегією Retreat відновлює HP і боєприпаси, доки перебуває в зоні бази.
    /// Потребує Collider з увімкненим isTrigger.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class TeamBase : MonoBehaviour
    {
        private static readonly Dictionary<Team, TeamBase> Bases = new Dictionary<Team, TeamBase>();

        [SerializeField] private Team team = Team.Red;
        [SerializeField] private float hpPerSecond = 2f;
        [SerializeField] private float ammoPerSecond = 1f;

        private readonly Dictionary<CombatAgent, float> ammoAccumulator = new Dictionary<CombatAgent, float>();

        public Team Team => team;

        public static TeamBase For(Team t)
        {
            return Bases.TryGetValue(t, out TeamBase b) ? b : null;
        }

        private void Reset() { GetComponent<Collider>().isTrigger = true; }
        private void OnEnable() { Bases[team] = this; }
        private void OnDisable() { if (Bases.TryGetValue(team, out TeamBase b) && b == this) Bases.Remove(team); }

        private void OnTriggerStay(Collider other)
        {
            CombatAgent agent = other.GetComponentInParent<CombatAgent>();
            if (agent == null || agent.Team != team || !agent.IsAlive) return;
            AgentBrain brain = agent.GetComponent<AgentBrain>();
            if (brain == null || brain.CurrentStrategy != Strategy.Retreat) return;

            ammoAccumulator.TryGetValue(agent, out float acc);
            acc += ammoPerSecond * Time.deltaTime;
            int whole = Mathf.FloorToInt(acc);
            ammoAccumulator[agent] = acc - whole;
            agent.Restore(hpPerSecond * Time.deltaTime, whole);
        }
    }
}
