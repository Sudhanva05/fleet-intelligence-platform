
import {
  LayoutDashboard,
  Truck,
  BarChart3,
  MapPin,
  Settings,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Truck size={28} />
        <h2>FleetIQ</h2>
      </div>

      <p className="sidebar-label">MAIN MENU</p>

      <nav className="sidebar-nav">
        <NavLink to="/" end className="nav-item">
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/vehicles" className="nav-item">
          <Truck size={20} />
          <span>Vehicles</span>
        </NavLink>

        <a href="#" className="nav-item">
          <MapPin size={20} />
          <span>Live Tracking</span>
        </a>

        <a href="#" className="nav-item">
          <BarChart3 size={20} />
          <span>Analytics</span>
        </a>

        <a href="#" className="nav-item">
          <Settings size={20} />
          <span>Settings</span>
        </a>
      </nav>
    </aside>
  );
};

export default Sidebar;
