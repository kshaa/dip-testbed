package diptestbed.domain

case class DIPTestbedConfig(
  testConfig: TestConfig,
  clusterized: Boolean,
  title: String,
  basePath: String
) {
  def makeTitle(suffix: String) = s"${title} - ${suffix}"

  def apiPrefix = s"/api"
  def appPrefix = s"/app"
  def assetsPrefix = s"/app/assets"

  def withAppPath(path: String) = s"${appPrefix}/${path.stripPrefix("/")}"
  def withAssetPath(path: String) = s"${assetsPrefix}/${path.stripPrefix("/")}"
}

object DIPTestbedConfig {
  def fromConfig(
    testConfig: TestConfig,
    clusterized: Option[Boolean],
    title: String,
    basePath: String
  ): DIPTestbedConfig =
    DIPTestbedConfig(
      testConfig,
      clusterized.getOrElse(false),
      title,
      basePath.stripSuffix("/"))
}
