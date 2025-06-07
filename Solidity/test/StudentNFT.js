const { expect } = require("chai");

describe("StudentBadgeNFT", function () {
  let contract;
  let owner;
  let addr1;

  beforeEach(async function () {
    const Contract = await ethers.getContractFactory("StudentBadgeNFT");
    [owner, addr1] = await ethers.getSigners();
    contract = await Contract.deploy();
    await contract.waitForDeployment();
  });

  it("should deploy and have correct name and symbol", async function () {
    expect(await contract.name()).to.equal("StudentBadgeNFT");
    expect(await contract.symbol()).to.equal("SBNFT");
  });

  it("should set badge cap and allow minting within limit", async function () {
    await contract.setBadgeCap("Top10Finisher", 2);

    const uri1 = "ipfs://badge1";
    const uri2 = "ipfs://badge2";

    await expect(
      contract.mintBadge(addr1.address, uri1, "Top10Finisher")
    ).to.emit(contract, "BadgeMinted");

    await expect(
      contract.mintBadge(addr1.address, uri2, "Top10Finisher")
    ).to.emit(contract, "BadgeMinted");

    expect(await contract.badgeMinted("Top10Finisher")).to.equal(2);
  });

  it("should not mint beyond badge cap", async function () {
    await contract.setBadgeCap("Top10Finisher", 1);
    await contract.mintBadge(addr1.address, "ipfs://badge1", "Top10Finisher");

    await expect(
      contract.mintBadge(addr1.address, "ipfs://badge2", "Top10Finisher")
    ).to.be.revertedWith("Minting limit reached for this badge");
  });

  it("should not allow non-owner to mint", async function () {
    await contract.setBadgeCap("CuriousCat", 1);

    await expect(
      contract.connect(addr1).mintBadge(addr1.address, "ipfs://badge", "CuriousCat")
    ).to.be.revertedWithCustomError(contract, "OwnableUnauthorizedAccount");
  });
});
