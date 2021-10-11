package iotfrisbee.domain

import org.scalatest.matchers.should.Matchers
import org.scalatest.freespec.AnyFreeSpec

class HashedPasswordSpec extends AnyFreeSpec with Matchers {
  "hashed password from string password should use random string every time" in {
    val password = "hunter2"
    val hash1 = HashedPassword.fromPassword(password)
    val hash2 = HashedPassword.fromPassword(password)
    hash1 should not be hash2
  }

  "hashed password should be verifiable after persistence" in {
    val password = "hunter2"
    val hash = HashedPassword.fromPassword(password)
    val serializedHash = hash.toSerializedString
    val unserializedHash = HashedPassword.fromSerializedString(serializedHash).get
    val verificationHash = HashedPassword.fromPassword(password, unserializedHash.salt)

    assert(hash === unserializedHash)
    assert(unserializedHash === verificationHash)
  }
}
