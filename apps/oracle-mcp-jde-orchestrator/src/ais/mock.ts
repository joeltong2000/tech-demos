import type {
  AisConnection,
  OrchestrationDescriptor,
  OrchestrationResult,
} from "./types";

/**
 * In-memory stand-in for a JDE E1 AIS server so the demo runs offline.
 *
 * The data model mirrors the E1 tables a real Orchestrator would touch:
 *  - F0101 (Address Book)        -> customers
 *  - F41021 (Item Location)      -> item availability per branch/plant
 *  - F4211 (Sales Order Detail)  -> sales orders
 *
 * Responses use JDE data-dictionary-style field names (sz* for strings,
 * mn* for math numeric) to match what a real AIS orchestration returns.
 */

interface F0101Row {
  an8: number; // Address Book number
  alph: string; // Alpha name
  city: string;
  sttl: string; // State
}

interface F41021Row {
  itm: string; // Item number
  litm: string; // Item description (borrowing the short name slot)
  mcu: string; // Branch/plant
  qtyOnHand: number;
  qtyCommitted: number;
}

interface F4211Line {
  itm: string;
  qty: number;
  unitPrice: number;
}

interface F4211Row {
  doco: number; // Order number
  an8: number; // Sold-to
  mcu: string; // Branch/plant
  status: string;
  lines: F4211Line[];
  orderedAt: string;
}

const f0101: F0101Row[] = [
  { an8: 4242, alph: "Capital Distributing", city: "Denver", sttl: "CO" },
  { an8: 4243, alph: "Eastern Manufacturing", city: "Pittsburgh", sttl: "PA" },
  { an8: 4244, alph: "Worldwide Restaurant Supply", city: "Chicago", sttl: "IL" },
  { an8: 4245, alph: "Capital City Grocers", city: "Sacramento", sttl: "CA" },
];

const f41021: F41021Row[] = [
  { itm: "210", litm: "Touring Bike, Red", mcu: "30", qtyOnHand: 131, qtyCommitted: 22 },
  { itm: "210", litm: "Touring Bike, Red", mcu: "20", qtyOnHand: 14, qtyCommitted: 14 },
  { itm: "220", litm: "Mountain Bike, Black", mcu: "30", qtyOnHand: 76, qtyCommitted: 5 },
  { itm: "630", litm: "Bike Helmet, Adult", mcu: "30", qtyOnHand: 412, qtyCommitted: 80 },
];

const ITEM_PRICES: Record<string, number> = {
  "210": 899.0,
  "220": 1249.0,
  "630": 54.5,
};

const CATALOG: OrchestrationDescriptor[] = [
  {
    name: "ORCH_CustomerSearch",
    description:
      "Search the Address Book (F0101) for customers whose name contains the given text.",
    inputs: [
      {
        name: "szSearchText",
        type: "string",
        required: true,
        description: "Text to match against the customer alpha name, e.g. 'Capital'.",
      },
    ],
  },
  {
    name: "ORCH_GetItemAvailability",
    description:
      "Return on-hand, committed and available quantity for an item in a branch/plant (F41021).",
    inputs: [
      {
        name: "szItemNumber",
        type: "string",
        required: true,
        description: "Short item number, e.g. '210'.",
      },
      {
        name: "szBranchPlant",
        type: "string",
        required: false,
        description: "Branch/plant, e.g. '30'. Omit to search all branch/plants.",
      },
    ],
  },
  {
    name: "ORCH_CreateSalesOrder",
    description:
      "Create a sales order (P4210 via Orchestrator) for a customer with a single order line.",
    inputs: [
      {
        name: "mnSoldTo",
        type: "number",
        required: true,
        description: "Sold-to Address Book number, e.g. 4242 (find one with ORCH_CustomerSearch).",
      },
      {
        name: "szBranchPlant",
        type: "string",
        required: true,
        description: "Branch/plant to ship from, e.g. '30'.",
      },
      {
        name: "szItemNumber",
        type: "string",
        required: true,
        description: "Item to order, e.g. '210'.",
      },
      {
        name: "mnQuantityOrdered",
        type: "number",
        required: true,
        description: "Quantity to order.",
      },
    ],
  },
  {
    name: "ORCH_GetOrderStatus",
    description: "Look up a sales order (F4211) by order number and return its status and lines.",
    inputs: [
      {
        name: "mnOrderNumber",
        type: "number",
        required: true,
        description: "Order number (DOCO) returned by ORCH_CreateSalesOrder, e.g. 8001.",
      },
    ],
  },
];

function aisError(message: string): OrchestrationResult {
  // Shape mirrors an AIS orchestration exception payload.
  return {
    message,
    exception: "OrchestrationException",
    timeStamp: new Date().toISOString(),
  };
}

export class MockAisConnection implements AisConnection {
  readonly label = "mock AIS (offline, in-memory E1 data)";
  readonly mode = "mock" as const;

  private readonly f4211: F4211Row[] = [
    {
      doco: 8000,
      an8: 4243,
      mcu: "30",
      status: "540 Shipped",
      lines: [{ itm: "630", qty: 25, unitPrice: 54.5 }],
      orderedAt: "2026-09-22T14:03:00Z",
    },
  ];
  private nextOrderNumber = 8001;

  async discoverOrchestrations(): Promise<OrchestrationDescriptor[]> {
    return CATALOG;
  }

  async invokeOrchestration(
    name: string,
    inputs: Record<string, string | number>,
  ): Promise<OrchestrationResult> {
    switch (name) {
      case "ORCH_CustomerSearch":
        return this.customerSearch(String(inputs.szSearchText ?? ""));
      case "ORCH_GetItemAvailability":
        return this.itemAvailability(
          String(inputs.szItemNumber ?? ""),
          inputs.szBranchPlant === undefined ? undefined : String(inputs.szBranchPlant),
        );
      case "ORCH_CreateSalesOrder":
        return this.createSalesOrder(
          Number(inputs.mnSoldTo),
          String(inputs.szBranchPlant ?? ""),
          String(inputs.szItemNumber ?? ""),
          Number(inputs.mnQuantityOrdered),
        );
      case "ORCH_GetOrderStatus":
        return this.orderStatus(Number(inputs.mnOrderNumber));
      default:
        return aisError(`Orchestration '${name}' is not published on this AIS server`);
    }
  }

  private customerSearch(searchText: string): OrchestrationResult {
    const needle = searchText.trim().toLowerCase();
    if (!needle) return aisError("szSearchText is required");
    const rowset = f0101
      .filter((r) => r.alph.toLowerCase().includes(needle))
      .map((r) => ({
        mnAddressNumber: r.an8,
        szAlphaName: r.alph,
        szCity: r.city,
        szState: r.sttl,
      }));
    return {
      "ServiceRequest1": {
        fs_DATABROWSE_F0101: {
          title: "Address Book Browse",
          data: { gridData: { summary: { records: rowset.length }, rowset } },
        },
      },
    };
  }

  private itemAvailability(item: string, branchPlant?: string): OrchestrationResult {
    const rows = f41021.filter(
      (r) => r.itm === item.trim() && (branchPlant === undefined || r.mcu === branchPlant.trim()),
    );
    if (rows.length === 0) {
      return aisError(
        `Item '${item}' not found${branchPlant ? ` in branch/plant '${branchPlant}'` : ""}`,
      );
    }
    return {
      "ServiceRequest1": {
        fs_P41202_W41202A: {
          title: "Item Availability",
          data: {
            gridData: {
              summary: { records: rows.length },
              rowset: rows.map((r) => ({
                szItemNumber: r.itm,
                szDescription: r.litm,
                szBranchPlant: r.mcu,
                mnQuantityOnHand: r.qtyOnHand,
                mnQuantityCommitted: r.qtyCommitted,
                mnQuantityAvailable: r.qtyOnHand - r.qtyCommitted,
              })),
            },
          },
        },
      },
    };
  }

  private createSalesOrder(
    soldTo: number,
    branchPlant: string,
    item: string,
    quantity: number,
  ): OrchestrationResult {
    const customer = f0101.find((r) => r.an8 === soldTo);
    if (!customer) return aisError(`Sold-to ${soldTo} not found in Address Book (F0101)`);
    const stock = f41021.find((r) => r.itm === item && r.mcu === branchPlant);
    if (!stock) return aisError(`Item '${item}' not stocked in branch/plant '${branchPlant}'`);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      return aisError("mnQuantityOrdered must be a positive number");
    }
    const available = stock.qtyOnHand - stock.qtyCommitted;
    if (quantity > available) {
      return aisError(
        `Insufficient availability for item '${item}' in '${branchPlant}': requested ${quantity}, available ${available}`,
      );
    }

    stock.qtyCommitted += quantity;
    const unitPrice = ITEM_PRICES[item] ?? 0;
    const order: F4211Row = {
      doco: this.nextOrderNumber++,
      an8: soldTo,
      mcu: branchPlant,
      status: "520 Ready to Print Pickslip",
      lines: [{ itm: item, qty: quantity, unitPrice }],
      orderedAt: new Date().toISOString(),
    };
    this.f4211.push(order);

    return {
      "ServiceRequest1": {
        fs_P4210_W4210A: {
          title: "Sales Order Entry",
          data: {
            szOrderType: "SO",
            szOrderNumber: String(order.doco),
            mnOrderNumber: order.doco,
            szSoldToName: customer.alph,
            szBranchPlant: branchPlant,
            mnOrderTotal: Number((quantity * unitPrice).toFixed(2)),
            szStatus: order.status,
          },
        },
      },
    };
  }

  private orderStatus(orderNumber: number): OrchestrationResult {
    const order = this.f4211.find((r) => r.doco === orderNumber);
    if (!order) return aisError(`Order ${orderNumber} not found in Sales Order Detail (F4211)`);
    const customer = f0101.find((r) => r.an8 === order.an8);
    return {
      "ServiceRequest1": {
        fs_P42101_W42101C: {
          title: "Sales Order Status",
          data: {
            mnOrderNumber: order.doco,
            szSoldToName: customer?.alph ?? String(order.an8),
            szBranchPlant: order.mcu,
            szStatus: order.status,
            jdOrderDate: order.orderedAt,
            gridData: {
              summary: { records: order.lines.length },
              rowset: order.lines.map((l, i) => ({
                mnLineNumber: (i + 1) * 1000,
                szItemNumber: l.itm,
                mnQuantityOrdered: l.qty,
                mnUnitPrice: l.unitPrice,
                mnExtendedPrice: Number((l.qty * l.unitPrice).toFixed(2)),
              })),
            },
          },
        },
      },
    };
  }
}
