
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

export const generateAnalyticsPDF = ({
  overview,
  speedTrend = [],
  fuelTrend = [],
  selectedRange = "all",
  appliedDates = {},
  selectedVehicle = "",
  vehicleAnalytics = null,
  vehicleHistory = [],
}) => {
  const doc = new jsPDF();

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  const formatNumber = (value) =>
    Number(value ?? 0).toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    });

  const formatDate = (value) => {
    if (!value) return "Not specified";

    return String(value).replace("T", " ");
  };

  const reportDate = new Date().toLocaleString("en-IN");

  const periodLabels = {
    all: "All Available Records",
    "24h": "Last 24 Hours",
    "7d": "Last 7 Days",
    "30d": "Last 30 Days",
    custom: "Custom Date Range",
  };

  const period = periodLabels[selectedRange] || "Selected Period";

  // --------------------------------------------------
  // REPORT HEADER
  // --------------------------------------------------

  doc.setFillColor(15, 23, 42);
  doc.rect(0, 0, pageWidth, 48, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");

  doc.text("FLEET INTELLIGENCE", 14, 20);

  doc.setFontSize(11);
  doc.setFont("helvetica", "normal");

  doc.text("Fleet Analytics Report", 14, 29);

  doc.setFontSize(9);
  doc.text(`Generated: ${reportDate}`, 14, 39);

  // --------------------------------------------------
  // REPORT PERIOD
  // --------------------------------------------------

  let y = 60;

  doc.setTextColor(30, 41, 59);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");

  doc.text("Report Information", 14, y);

  y += 9;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(`Reporting Period: ${period}`, 14, y);

  y += 7;

  if (appliedDates.startTime || appliedDates.endTime) {
    doc.text(
      `Start: ${formatDate(appliedDates.startTime)}`,
      14,
      y
    );

    y += 7;

    doc.text(
      `End: ${formatDate(appliedDates.endTime)}`,
      14,
      y
    );

    y += 7;
  }

  if (selectedVehicle) {
    doc.setFont("helvetica", "bold");
    doc.text(`Vehicle ID: ${selectedVehicle}`, 14, y);
    y += 7;
  }

  // --------------------------------------------------
  // FLEET SUMMARY
  // --------------------------------------------------

  y += 5;

  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");

  doc.text(
    selectedVehicle ? "Selected Vehicle Performance" : "Fleet Summary",
    14,
    y
  );

  const summary = selectedVehicle && vehicleAnalytics
    ? [
        ["Total Events", formatNumber(vehicleAnalytics.total_events)],
        ["Average Speed", `${formatNumber(vehicleAnalytics.average_speed)} km/h`],
        ["Minimum Speed", `${formatNumber(vehicleAnalytics.minimum_speed)} km/h`],
        ["Maximum Speed", `${formatNumber(vehicleAnalytics.maximum_speed)} km/h`],
        ["Average Fuel", `${formatNumber(vehicleAnalytics.average_fuel)} %`],
      ]
    : [
        ["Total Events", formatNumber(overview?.total_events)],
        ["Total Vehicles", formatNumber(overview?.total_vehicles)],
        ["Average Speed", `${formatNumber(overview?.average_speed)} km/h`],
        ["Average Fuel", `${formatNumber(overview?.average_fuel)} %`],
      ];

  autoTable(doc, {
    startY: y + 5,
    head: [["Metric", "Value"]],
    body: summary,
    theme: "grid",
    headStyles: {
      fillColor: [15, 23, 42],
    },
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
  });

  y = doc.lastAutoTable.finalY + 12;

  // --------------------------------------------------
  // SPEED TREND
  // --------------------------------------------------

  const speedRows = selectedVehicle
    ? vehicleHistory.map((record) => [
        formatDate(record.time || record.timestamp),
        formatNumber(record.speed),
      ])
    : speedTrend.map((record) => [
        formatDate(record.time),
        formatNumber(record.average_speed),
      ]);

  if (y > pageHeight - 45) {
    doc.addPage();
    y = 20;
  }

  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");

  doc.text(
    selectedVehicle ? "Vehicle Speed History" : "Fleet Speed Trend",
    14,
    y
  );

  autoTable(doc, {
    startY: y + 5,
    head: [["Timestamp", "Speed (km/h)"]],
    body: speedRows,
    theme: "striped",
    headStyles: {
      fillColor: [3, 105, 161],
    },
    styles: {
      fontSize: 8,
      cellPadding: 2.5,
    },
    showHead: "everyPage",
  });

  y = doc.lastAutoTable.finalY + 12;

  // --------------------------------------------------
  // FUEL TREND
  // --------------------------------------------------

  const fuelRows = selectedVehicle
    ? vehicleHistory.map((record) => [
        formatDate(record.time || record.timestamp),
        formatNumber(record.fuel ?? record.fuel_level),
      ])
    : fuelTrend.map((record) => [
        formatDate(record.time),
        formatNumber(record.average_fuel),
      ]);

  if (y > pageHeight - 45) {
    doc.addPage();
    y = 20;
  }

  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");

  doc.text(
    selectedVehicle ? "Vehicle Fuel History" : "Fleet Fuel Trend",
    14,
    y
  );

  autoTable(doc, {
    startY: y + 5,
    head: [["Timestamp", "Fuel Level (%)"]],
    body: fuelRows,
    theme: "striped",
    headStyles: {
      fillColor: [5, 150, 105],
    },
    styles: {
      fontSize: 8,
      cellPadding: 2.5,
    },
    showHead: "everyPage",
  });

  // --------------------------------------------------
  // PAGE NUMBERS
  // --------------------------------------------------

  const pageCount = doc.internal.getNumberOfPages();

  for (let page = 1; page <= pageCount; page++) {
    doc.setPage(page);

    doc.setFontSize(8);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100, 116, 139);

    doc.text(
      `Fleet Intelligence Platform | Page ${page} of ${pageCount}`,
      pageWidth / 2,
      pageHeight - 8,
      { align: "center" }
    );
  }

  // --------------------------------------------------
  // DOWNLOAD
  // --------------------------------------------------

  const filename = selectedVehicle
    ? `vehicle-report-${selectedVehicle.slice(0, 8)}.pdf`
    : "fleet-analytics-report.pdf";

  doc.save(filename);
};
