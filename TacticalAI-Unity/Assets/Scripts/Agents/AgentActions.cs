using TacticalAI.Core;
using TacticalAI.Environment;
using UnityEngine;

namespace TacticalAI.Agents
{
    /// <summary>
    /// Виконання обраної стратегії (прототип; переміщення по прямій, без NavMesh).
    /// Attack — рух до найближчого виявленого ворога до дистанції вогню, вогонь;
    /// Defense — рух до найближчої зони укриття, вогонь з неї;
    /// Retreat — рух до власної бази без вогню (відновлення ресурсу виконує TeamBase).
    /// </summary>
    [RequireComponent(typeof(CombatAgent), typeof(AgentBrain))]
    public class AgentActions : MonoBehaviour
    {
        [SerializeField] private float speed = 2f;
        [SerializeField] private float fireRange = 15f;
        [SerializeField] private float fireInterval = 1f;
        [SerializeField] private float baseHitChance = 0.35f;
        [SerializeField] private float movingShooterFactor = 0.6f;
        [SerializeField] private float targetInCoverFactor = 0.5f;
        [SerializeField] private float damage = 25f;

        private CombatAgent self;
        private AgentBrain brain;
        private float fireTimer;

        private void Awake()
        {
            self = GetComponent<CombatAgent>();
            brain = GetComponent<AgentBrain>();
        }

        private void Update()
        {
            if (!self.IsAlive) return;
            self.MovedThisStep = false;
            CombatAgent enemy = brain.NearestEnemy != null && brain.NearestEnemy.IsAlive ? brain.NearestEnemy : null;

            switch (brain.CurrentStrategy)
            {
                case Strategy.Attack:
                    if (enemy == null) MoveTowards(transform.position + Forward());
                    else if (Vector3.Distance(transform.position, enemy.transform.position) > fireRange) MoveTowards(enemy.transform.position);
                    TryFire(enemy);
                    break;
                case Strategy.Defense:
                    CoverZone cover = CoverZone.Nearest(transform.position);
                    if (cover != null && !self.InCover) MoveTowards(cover.transform.position);
                    TryFire(enemy);
                    break;
                case Strategy.Retreat:
                    TeamBase home = TeamBase.For(self.Team);
                    if (home != null) MoveTowards(home.transform.position);
                    break;
            }
        }

        private Vector3 Forward()
        {
            TeamBase enemyBase = TeamBase.For(self.Team == Team.Red ? Team.Blue : Team.Red);
            return enemyBase != null ? (enemyBase.transform.position - transform.position).normalized : transform.forward;
        }

        private void MoveTowards(Vector3 target)
        {
            Vector3 next = Vector3.MoveTowards(transform.position, target, speed * Time.deltaTime);
            if ((next - transform.position).sqrMagnitude > 1e-8f) self.MovedThisStep = true;
            transform.position = next;
        }

        private void TryFire(CombatAgent target)
        {
            fireTimer -= Time.deltaTime;
            if (target == null || fireTimer > 0f) return;
            float d = Vector3.Distance(transform.position, target.transform.position);
            if (d > fireRange || !self.TryConsumeAmmo()) return;
            fireTimer = fireInterval;

            float p = baseHitChance * (1f - 0.5f * d / fireRange);
            if (self.MovedThisStep) p *= movingShooterFactor;
            if (target.InCover) p *= targetInCoverFactor;
            if (Random.value < p) target.TakeDamage(damage);
        }
    }
}
