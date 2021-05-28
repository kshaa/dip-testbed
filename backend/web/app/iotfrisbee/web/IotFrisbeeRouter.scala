package iotfrisbee.web

import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._
import iotfrisbee.domain._
import iotfrisbee.web.controllers._
import iotfrisbee.web.sird.UUIDBinding.uuid

class IotFrisbeeRouter(
  homeController: HomeController,
  userController: UserController,
  diskGolfTrackController: DiskGolfTrackController,
  hardwareController: HardwareController,
  hardwareMessageController: HardwareMessageController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.index
    case GET(p"/status") => homeController.status

    // Users
    case POST(p"/users")                => userController.createUser
    case GET(p"/users")                 => userController.getUsers
    case GET(p"/users/${uuid(userId)}") => userController.getUser(UserId(userId))

    // Disk golf track
    case POST(p"/disk-golf-tracks")                => diskGolfTrackController.createDiskGolfTrack
    case GET(p"/disk-golf-tracks")                 => diskGolfTrackController.getDiskGolfTracks
    case GET(p"/disk-golf-tracks/${uuid(userId)}") => diskGolfTrackController.getDiskGolfTrack(DiskGolfTrackId(userId))

    // Hardware
    case POST(p"/hardwares")                    => hardwareController.createHardware
    case GET(p"/hardwares")                     => hardwareController.getHardwares
    case GET(p"/hardwares/${uuid(hardwareId)}") => hardwareController.getHardware(HardwareId(hardwareId))

    // Hardware message
    case POST(p"/hardware-messages") => hardwareMessageController.createHardwareMessage
    case GET(p"/hardware-messages")  => hardwareMessageController.getHardwareMessages
    case GET(p"/hardware-messages/${uuid(hardwareMessageId)}") =>
      hardwareMessageController.getHardwareMessage(HardwareMessageId(hardwareMessageId))
  }
}
