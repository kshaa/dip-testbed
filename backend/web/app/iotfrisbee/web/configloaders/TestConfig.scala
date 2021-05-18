package iotfrisbee.web.configloaders

import iotfrisbee.domain.{TestConfig => DomainTestConfig}
import com.typesafe.config.Config
import play.api.{ConfigLoader, Configuration}

object TestConfig {
  implicit val testConfigLoader: ConfigLoader[DomainTestConfig] = (rootConfig: Config, path: String) => {
    Option
      .when(rootConfig.hasPath(path))(Configuration(rootConfig.getConfig(path)))
      .map(config =>
        DomainTestConfig.fromConfig(
          enabled = config.getOptional[Boolean]("enabled"),
          testName = config.getOptional[String]("name"),
        ),
      )
      .getOrElse(DomainTestConfig.empty)
  }
}
