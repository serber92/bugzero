const axios = require("axios");
const { htmlToText } = require("html-to-text");
const handler = require("./libs/handler-lib");
const eventManagement = require("./libs/eventManagement-lib");

const VENDORS = require("./vendors");
const { readSecret } = require("./libs/secret-lib");

module.exports.bugEventProcessor = handler(async (event, context, db) => {
  try {
    // Check that the SN secret exists
    const serviceNowSettings = await db.setting.findByPk("servicenow");
    console.log("serviceNowSettings", serviceNowSettings);
    if (
      !serviceNowSettings ||
      !serviceNowSettings.value ||
      !serviceNowSettings.value.secretId
    )
      throw new Error("Missing ServiceNow setting");

    const snSecret = await readSecret(serviceNowSettings.value.secretId);
    console.log("snSecret", snSecret);
    if (!snSecret) throw new Error("Missing ServiceNow secret");
    const snAuthToken = Buffer.from(
      `${snSecret.user}:${snSecret.pass}`
    ).toString("base64");
    console.log("snAuthToken", snAuthToken);
    console.log("serviceNowSettings", serviceNowSettings);
    const bugs = await db.bug.findAll({
      where: {
        processed: false,
      },
    });
    const vendorSettings = await db.setting.findAll({
      where: {
        type: "vendor",
      },
    });

    const vendors = {};
    vendorSettings.map((vendorSetting) => {
      vendors[vendorSetting.id] = vendorSetting;
    });

    console.log(`Bugs: ${bugs.length}`);

    for (let i = 0; i < bugs.length; i++) {
      const bug = bugs[i];
      const managedProduct = await db.managedProduct.findByPk(
        bug.managedProductId
      );
      const vendorSetting = vendors[bug.vendorId].value;
      const vendor = VENDORS[managedProduct.vendorId];
      console.log("vendor", vendor);
      console.log("bug", bug);

      console.log("managedProduct", managedProduct);

      // Create problem ticket
      const url = `${serviceNowSettings.value.snApiUrl}/api/now/table/x_buz_bzero_web_service?sysparm_fields=sys_id`;
      let data = null;
      console.log(
        "managedProduct.vendorPriorities",
        managedProduct.vendorPriorities
      );

      const vendorPriority = vendor.priorities.find((el) => {
        return (
          el.label.toLowerCase() === bug.priority.toLowerCase() ||
          el.value.toLowerCase() === bug.priority.toLowerCase() ||
          el.bugValue.toLowerCase() === bug.priority.toLowerCase()
        );
      });
      console.log("vendorPriority", vendorPriority);

      const mpPriority = managedProduct.vendorPriorities.find(
        (el) =>
          el.vendorPriority.toLowerCase() ===
            vendorPriority.value.toLowerCase() ||
          el.vendorPriority.toLowerCase() ===
            vendorPriority.value.toLowerCase() ||
          el.vendorPriority.toLowerCase() ===
            vendorPriority.bugValue.toLowerCase()
      );
      // If priority does not match/exist. Skip bug and mark as processed.
      if (!mpPriority) {
        bug.processed = true;
        await bug.save();
        continue;
      }
      const snPriority = mpPriority.snPriority;

      console.log("snPriority", snPriority);

      const [impact, urgency] = snPriority.split("|");

      let status = bug.status || "";
      // convert bug.priorites from value to label

      console.log("bug.priority", bug.priority);

      let priority = bug.priority;

      let description = "";
      // Convert HTML to text
      try {
        description = htmlToText(bug.description, {
          wordwrap: 130,
          preserveNewlines: true,
        });
      } catch (e) {
        console.log("HTML TO TEXT ERROR");
        console.error(e);
        eventManagement.sendEvent(e);
      }

      // Strip out any consecutive newlines
      description = description.replace(/(\r\n|\r|\n){2,}/g, "$1\n");

      // Strip time off ISO datetime
      console.log(
        "bug.vendorCreatedDate",
        typeof bug.vendorCreatedDate,
        bug.vendorCreatedDate
      );
      console.log(
        "bug.vendorLastUpdatedDate",
        typeof bug.vendorLastUpdatedDate,
        bug.vendorLastUpdatedDate
      );
      let vendorCreatedDate, vendorLastUpdatedDate;

      // handle invalid dates/null dates
      try {
        vendorCreatedDate = bug.vendorCreatedDate
          ? bug.vendorCreatedDate.toISOString().slice(0, 10)
          : null;
      } catch (e) {
        // Invalid date ie Null, set as blank
        vendorCreatedDate = "";
      }

      // handle invalid dates/null dates
      try {
        vendorLastUpdatedDate = bug.vendorLastUpdatedDate
          ? bug.vendorLastUpdatedDate.toISOString().slice(0, 10)
          : null;
      } catch (e) {
        vendorLastUpdatedDate = "";
      }

      switch (managedProduct.vendorId) {
        case "cisco":
          // hardware payload
          data = {
            u_bug_category: "Hardware",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_operating_system: "",
            u_os_version: "",
            // u_product_model: managedProduct.snProductId,
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_support_cases: bug.vendorData.supportCasesCount || "",
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status,
            u_vendor_url: bug.bugUrl,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "hpe":
          // hardware payload
          data = {
            u_bug_category: "Hardware",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: `${bug.knownAffectedHardware} ${bug.knownAffectedOs}`,
            u_known_fixed_releases: "",
            u_operating_system: "",
            u_os_version: "",
            u_product_model: managedProduct.snProductId,
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status,
            u_vendor_url: bug.bugUrl,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "rh":
          // OS payload
          data = {
            u_bug_category: "Software",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_vendor_resolution:
              managedProduct.vendorData &&
              managedProduct.vendorData.vendorResolution
                ? managedProduct.vendorData.vendorResolution
                : "",
            u_known_affected_releases: bug.version ? bug.version.join(",") : "",
            u_known_fixed_releases: "",
            u_operating_system: "Linux Red Hat",
            u_os_version: bug.version ? bug.version.join(",") : "",
            // u_product_model: managedProduct.snProductId,
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status,
            u_vendor_url: bug.bugUrl,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "msft":
          // OS payload
          data = {
            u_bug_category: "Software",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "msft365":
          // OS payload
          data = {
            u_bug_category: "Software",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "vmware":
          // OS payload

          data = {
            u_bug_category: "Software",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_kb_view_count:
              bug.vendorData && bug.vendorData.articleViews
                ? bug.vendorData.articleViews
                : "", // vendor specific
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };

          break;
        case "aws":
          // OS payload

          data = {
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };

          break;
        case "mongodb":
          // OS payload

          data = {
            u_bug_category: "Software",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_resolution:
              managedProduct.vendorData &&
              managedProduct.vendorData.vendorResolution
                ? managedProduct.vendorData.vendorResolution
                : "",
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };

          break;
        case "fortinet":
          // OS payload

          data = {
            u_bug_category: "Hardware",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };

          break;
        case "veeam":
          // OS payload

          data = {
            u_bug_category: "Hardware",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };
          break;
        case "netapp":
          // OS payload

          data = {
            u_bug_category: "Hardware",
            u_ci_filter: bug.snCiFilter,
            u_ci_table: bug.snCiTable,
            u_description: description,
            u_impact: impact,
            u_known_affected_releases: bug.knownAffectedReleases || "",
            u_known_fixed_releases: bug.knownFixedReleases || "",
            u_short_description: bug.summary,
            u_urgency: urgency,
            u_vendor: vendorSetting.snCompanySysId,
            u_vendor_announcement_date: vendorCreatedDate,
            u_vendor_bug_id: bug.bugId,
            u_vendor_severity: priority,
            u_vendor_status: status || "Unspecified",
            u_vendor_url: bug.bugUrl,
            u_vendor_last_update_date: vendorLastUpdatedDate,
          };

          break;

        default:
          break;
      }
      console.log("created type", typeof bug.createdAt);
      // Do not update impact/urgency if bug is being updated.
      if (bug.createdAt.getTime() !== bug.updatedAt.getTime()) {
        console.log(
          `Bug was updated! Created/Updated: ${bug.updatedAt.getTime()}/${bug.createdAt.getTime()}`
        );
        delete data.u_impact;
        delete data.u_urgency;
      } else console.log("Bug was created!");

      console.log("creating ticket", data);
      const config = {
        headers: {
          Authorization: `Basic ${snAuthToken}`,
        },
        timeout: 15000,
      };
      await axios.post(url, data, config);
      console.log(
        `🐛 [${managedProduct.vendorId}][${bug.bugId}]: ${bug.summary}`
      );
      bug.processed = true;
      await bug.save();
    } // end bugs map
    return bugs;
  } catch (e) {
    console.error(e);
    eventManagement.sendEvent(e);
  }
});
