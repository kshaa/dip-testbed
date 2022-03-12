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

  def withBase(path: String): String = s"${basePath}/${path.stripPrefix("/")}"
  def withAppPath(path: String): String = withBase(s"${appPrefix}/${path.stripPrefix("/")}")
  def withAssetPath(path: String): String = withBase(s"${assetsPrefix}/${path.stripPrefix("/")}")
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
