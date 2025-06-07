const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("StudentNFTModule", (m) => {
  const studentBadgeNFT = m.contract("StudentBadgeNFT", [m.getAccount(0)]);

// Set unique IDs for each call to avoid IGN702 error
  m.call(studentBadgeNFT, "setBadgeCap", ["TopQuizzer", 100], { id: "SetCapTopQuizzer" });
  m.call(studentBadgeNFT, "setBadgeCap", ["PitchMaster", 50], { id: "SetCapPitchMaster" });
  m.call(studentBadgeNFT, "setBadgeCap", ["TopInnovator", 25], { id: "SetCapTopInnovator" });

  return { studentBadgeNFT };
});
