package iotfrisbee.domain

import java.util.Base64
import com.roundeights.hasher.Implicits._

case class PasswordRaw(value: String) {
  def hashed(salt: Salt, iterations: Int) = {
    val hash = value.pbkdf2(salt.value, iterations)
  }
}

object PasswordRaw {
  def randomBytes(bytes: Int): Array[Byte] =
    Array.fill(bytes)((scala.util.Random.nextInt(256) - 128).toByte)

  def randomSalt(bytes: Int): Salt =
    Salt(Base64.getEncoder.encodeToString(randomBytes(bytes)))
}

case class PasswordHashed(salt: Salt, hash: Hash) {}

case class Salt(value: String)

case class Hash(value: String)
