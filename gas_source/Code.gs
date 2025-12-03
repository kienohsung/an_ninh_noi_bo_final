// --- CONFIGURATION ---
var SHEET_ID = '1zenHc1PuDHvVcuctJnTVp8tdD-3xWMf36ozynLk7jHw'; // Replace with actual Sheet ID
var SHEET_NAME_DATA = 'Câu trả lời biểu mẫu 1'; // Or whatever the target sheet is
var SHEET_NAME_USERS = 'Users'; // Columns: A=ID, B=Name
var SHEET_NAME_VENDORS = 'Vendors'; // Optional: Column A=Vendor Name

// --- WEB APP ENTRY POINT ---
function doGet(e) {
  var template = HtmlService.createTemplateFromFile('index');
  return template.evaluate()
      .setTitle('Đăng Ký Khách - Ohsung Vina')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// --- DATA FETCHING FOR TEMPLATE ---
function getUsersList() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME_USERS);
  if (!sheet) return []; // Return empty if sheet doesn't exist
  
  var data = sheet.getDataRange().getValues();
  var users = [];
  // Assume Row 1 is Header
  for (var i = 1; i < data.length; i++) {
    if (data[i][0]) { // If ID exists
      users.push({
        id: data[i][0].toString(),
        name: data[i][1]
      });
    }
  }
  return users;
}

function getVendorsList() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME_VENDORS);
  if (!sheet) return [];
  
  var data = sheet.getDataRange().getValues();
  var vendors = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][0]) {
      vendors.push(data[i][0].toString());
    }
  }
  return vendors;
}

// --- FORM PROCESSING ---
function processForm(formObject) {
  try {
    var ss = SpreadsheetApp.openById(SHEET_ID);
    var sheet = ss.getSheetByName(SHEET_NAME_DATA);
    
    // Format Timestamp: dd/MM/yyyy HH:mm:ss
    // Note: Python backend expects specific format. 
    // GAS Timezone should be set to GMT+7 in Project Settings.
    var timestamp = Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy HH:mm:ss");
    
    // Prepare Row Data
    // Mapping based on Python Service:
    // 0: Timestamp
    // 1: UserID
    // 2: GuestName
    // 3: CCCD
    // 4: Vendor
    // 5: Plate
    // 6: JobDetail
    // 7: SYNC_STATUS (Empty)
    
    var rowData = [
      timestamp,
      formObject.userId,
      formObject.guestName,
      "'" + formObject.cccd, // Force string for CCCD to avoid scientific notation if long
      formObject.vendor,
      formObject.plateNo,
      formObject.jobDetail,
      "", // Email (Index 7) - Empty
      formObject.estimatedTime, // test (Index 8) - Used for Estimated Time
      "", // Cột 9 (Index 9) - Empty
      "" // SYNC_STATUS (Index 10) - Empty
    ];
    
    sheet.appendRow(rowData);
    
    return { status: 'success' };
    
  } catch (e) {
    Logger.log(e.toString());
    throw new Error("Lỗi Server: " + e.message);
  }
}
