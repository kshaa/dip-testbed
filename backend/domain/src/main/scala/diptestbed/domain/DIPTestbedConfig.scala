package diptestbed.domain

import java.util.UUID
import scala.concurrent.duration.{DurationInt, FiniteDuration}

case class DIPTestbedConfig(
  testConfig: TestConfig,
  clusterized: Boolean,
  title: String,
  basePath: String,
  adminUsername: Option[String],
  adminPassword: Option[String],
  adminEnabled: Boolean,
  heartbeatingTime: FiniteDuration,
  heartbeatingTimeout: FiniteDuration,
  heartbeatsInCycle: Int,
  maxStreamTime: FiniteDuration,
  cameraInitTimeout: FiniteDuration
) {
  def makeTitle(contentTitle: String) = s"${contentTitle} · ${title}"

  def apiPrefix = s"/api"
  def appPrefix = s"/app"
  def assetsPrefix = s"/app/assets"

  def withVersionApiPrefix(version: String) = s"${apiPrefix}/${version}"
  def withBase(path: String): String = s"${basePath}/${path.stripPrefix("/")}"
  def withAppPath(path: String): String = withBase(s"${appPrefix}/${path.stripPrefix("/")}")
  def withApiPath(path: String, version: String = "v1"): String =
    withBase(s"${apiPrefix}/${version}/${path.stripPrefix("/")}")
  def withAssetPath(path: String): String = withBase(s"${assetsPrefix}/${path.stripPrefix("/")}")

  def adminUser: Option[User] =
    adminUsername.map(User(
      UserId(UUID.randomUUID()),
      _,
      isManager = true,
      isLabOwner = true,
      isDeveloper = true
    ))
}

object DIPTestbedConfig {
  def fromConfig(
    testConfig: TestConfig,
    clusterized: Option[Boolean],
    title: String,
    basePath: String,
    adminUsername: Option[String] = None,
    adminPassword: Option[String] = None,
    adminEnabled: Option[Boolean] = None,
    heartbeatingTime: Option[FiniteDuration] = None,
    heartbeatingTimeout: Option[FiniteDuration] = None,
    heartbeatsInCycle: Option[Int] = None,
    maxStreamTime: Option[FiniteDuration] = None,
    cameraInitTimeout: Option[FiniteDuration] = None
  ): DIPTestbedConfig =
    DIPTestbedConfig(
      testConfig,
      clusterized.getOrElse(false),
      title,
      basePath.stripSuffix("/"),
      adminUsername,
      adminPassword,
      adminEnabled.getOrElse(false),
      heartbeatingTime.getOrElse(10.seconds),
      heartbeatingTimeout.getOrElse(8.seconds),
      heartbeatsInCycle.getOrElse(3),
      maxStreamTime.getOrElse(15.minutes),
      cameraInitTimeout.getOrElse(3.seconds)
    )
}
