package diptestbed.web.config

import diptestbed.domain.{DIPTestbedConfig => DomainDIPTestbedConfig, TestConfig => DomainTestConfig}
import diptestbed.web.config.TestConfig._
import com.typesafe.config.Config
import play.api.{ConfigLoader, Configuration}

import scala.concurrent.duration.FiniteDuration

object DIPTestbedConfig {
  implicit val dipTestbedConfigLoader: ConfigLoader[DomainDIPTestbedConfig] = (rootConfig: Config, path: String) => {
    val config: Configuration = Configuration(rootConfig.getConfig(path))

    DomainDIPTestbedConfig.fromConfig(
      config.get[DomainTestConfig]("test"),
      config.getOptional[Boolean]("clusterized"),
      config.get[String]("title"),
      config.get[String]("basePath"),
      config.get[Option[String]]("adminUsername"),
      config.get[Option[String]]("adminPassword"),
      config.get[Option[Boolean]]("adminEnabled"),
      config.get[Option[FiniteDuration]]("heartbeatingTime"),
      config.get[Option[FiniteDuration]]("heartbeatingTimeout"),
      config.get[Option[Int]]("heartbeatsInCycle"),
      config.get[Option[FiniteDuration]]("maxStreamTime"),
      config.get[Option[FiniteDuration]]("cameraInitTimeout"),
    )
  }
}
