package diptestbed.web

import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._
import diptestbed.domain._
import diptestbed.web.controllers._
import diptestbed.web.sird.UUIDBinding.uuid

class DIPTestbedRouter(
  homeController: HomeController,
  userController: UserController,
  hardwareController: HardwareController,
  softwareController: SoftwareController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.index
    case GET(p"/status") => homeController.status

    // Users
    case POST(p"/user")                => userController.createUser
    case GET(p"/user")                 => userController.getUsers
    case GET(p"/user/${uuid(userId)}") => userController.getUser(UserId(userId))

    // Hardware
    case POST(p"/hardware")                            => hardwareController.createHardware
    case GET(p"/hardware")                             => hardwareController.getHardwares
    case GET(p"/hardware/${uuid(hardwareId)}")         => hardwareController.getHardware(HardwareId(hardwareId))
    case GET(p"/hardware/${uuid(hardwareId)}/control") => hardwareController.controlHardware(HardwareId(hardwareId))
    case POST(p"/hardware/${uuid(hardwareId)}/upload/software/${uuid(softwareId)}") =>
      hardwareController.uploadHardwareSoftware(HardwareId(hardwareId), SoftwareId(softwareId))
    case GET(p"/hardware/${uuid(hardwareId)}/monitor/serial") =>
      hardwareController.listenHardwareSerialMonitor(HardwareId(hardwareId), None)

    // Software
    case POST(p"/software")                             => softwareController.createSoftware
    case GET(p"/software")                              => softwareController.getSoftwareMetas
    case GET(p"/software/${uuid(softwareId)}/download") => softwareController.getSoftware(SoftwareId(softwareId))

  }
}
