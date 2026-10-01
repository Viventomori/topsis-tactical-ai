using System.Collections.Generic;
using UnityEngine;

namespace TacticalAI.Agents
{
    /// <summary>
    /// Параметри персонажа, з яких програмно зчитуються значення критеріїв (запас боєприпасів, HP, укриття).
    /// Усі живі агенти реєструються в статичному списку для швидкого пошуку союзників і ворогів.
    /// </summary>
    public class CombatAgent : MonoBehaviour
    {
        public static readonly List<CombatAgent> All = new List<CombatAgent>();

        [SerializeField] private Team team = Team.Red;
        [SerializeField] private float maxHp = 100f;
        [SerializeField] private int maxAmmo = 30;

        public Team Team => team;
        public float MaxHp => maxHp;
        public int MaxAmmo => maxAmmo;
        public float Hp { get; private set; }
        public int Ammo { get; private set; }
        public bool IsAlive => Hp > 0f;

        /// <summary>Кількість зон укриття, у яких зараз перебуває агент (встановлює CoverZone).</summary>
        public int CoverCount { get; set; }
        public bool InCover => CoverCount > 0;

        /// <summary>Чи рухався агент у поточному кадрі (впливає на ймовірність влучання).</summary>
        public bool MovedThisStep { get; set; }

        private void Awake()
        {
            Hp = maxHp;
            Ammo = maxAmmo;
        }

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        public bool TryConsumeAmmo()
        {
            if (Ammo <= 0) return false;
            Ammo--;
            return true;
        }

        public void TakeDamage(float amount)
        {
            if (!IsAlive) return;
            Hp = Mathf.Max(0f, Hp - amount);
            if (!IsAlive) gameObject.SetActive(false);
        }

        public void Restore(float hp, int ammo)
        {
            Hp = Mathf.Min(maxHp, Hp + hp);
            Ammo = Mathf.Min(maxAmmo, Ammo + ammo);
        }
    }
}
