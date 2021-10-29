package diptestbed.web

import play.api._
import play.api.ApplicationLoader.Context
import cats.effect.unsafe.implicits.global

class DIPTestbedLoader extends ApplicationLoader {
  def load(context: Context): Application = {
    LoggerConfigurator(context.environment.classLoader)
      .foreach(
        _.configure(
          context.environment,
          context.initialConfiguration,
          Map.empty,
        ),
      )

    val dipTestbedModule = new DIPTestbedModule(context)
    dipTestbedModule.applicationEvolutions
    dipTestbedModule.application
  }
}
