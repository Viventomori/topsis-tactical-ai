using System.Collections.Generic;
using TacticalAI.Agents;
using UnityEngine;

namespace TacticalAI.Environment
{
    /// <summary>
    /// Зона укриття: тригер ділянки місцевості, що задає значення критерію S5 (1 — в укритті, 0 — відкрита ділянка).
    /// Потребує Collider з увімкненим isTrigger; агенти — Rigidbody (isKinematic) і Collider.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class CoverZone : MonoBehaviour
    {
        public static readonly List<CoverZone> All = new List<CoverZone>();

        private void Reset() { GetComponent<Collider>().isTrigger = true; }
        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        private void OnTriggerEnter(Collider other)
        {
            CombatAgent agent = other.GetComponentInParent<CombatAgent>();
            if (agent != null) agent.CoverCount++;
        }

        private void OnTriggerExit(Collider other)
        {
            CombatAgent agent = other.GetComponentInParent<CombatAgent>();
            if (agent != null) agent.CoverCount = Mathf.Max(0, agent.CoverCount - 1);
        }

        public static CoverZone Nearest(Vector3 position)
        {
            CoverZone best = null;
            float bestD = float.MaxValue;
            foreach (CoverZone z in All)
            {
                float d = Vector3.Distance(position, z.transform.position);
                if (d < bestD) { bestD = d; best = z; }
            }
            return best;
        }
    }
}
