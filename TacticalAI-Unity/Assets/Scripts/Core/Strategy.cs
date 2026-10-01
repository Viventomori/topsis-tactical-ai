namespace TacticalAI.Core
{
    /// <summary>Множина стратегій A = {A1, A2, A3}. Порядок значень задає порядок рядків матриці рішень
    /// та правило вирішення рівності коефіцієнтів C_i (обирається перша стратегія).</summary>
    public enum Strategy
    {
        Attack = 0,
        Defense = 1,
        Retreat = 2
    }
}
