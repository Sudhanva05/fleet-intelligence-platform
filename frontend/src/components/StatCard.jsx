
const StatCard = ({ title, value, unit, icon: Icon, color }) => {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <span>{title}</span>
        <div className={`stat-icon ${color}`}>
          <Icon size={20} />
        </div>
      </div>

      <div className="stat-value">
        {value ?? "--"}
        {unit && <span>{unit}</span>}
      </div>
    </div>
  );
};

export default StatCard;
