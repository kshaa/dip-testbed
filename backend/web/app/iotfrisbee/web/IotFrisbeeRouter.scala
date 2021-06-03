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
  diskGolfDiskController: DiskGolfDiskController,
  diskGolfBasketController: DiskGolfBasketController,
  diskGolfGameController: DiskGolfGameController,
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
    case GET(p"/hardware-messages")  => hardwareMessageController.getHardwareMessages(None)
    case GET(p"/hardware-messages/${uuid(hardwareMessageId)}") =>
      hardwareMessageController.getHardwareMessage(HardwareMessageId(hardwareMessageId))
    case GET(p"/hardwares/${uuid(hardwareId)}/messages") =>
      hardwareMessageController.getHardwareMessages(Some(HardwareId(hardwareId)))
    case GET(p"/hardwares/${uuid(hardwareId)}/messages/subscribe") =>
      hardwareMessageController.subscribeHardwareMessages(HardwareId(hardwareId))

    // Disk golf disks
    case POST(p"/disk-golf-disks")                => diskGolfDiskController.createDiskGolfDisk
    case GET(p"/disk-golf-disks")                 => diskGolfDiskController.getDiskGolfDisks
    case GET(p"/disk-golf-disks/${uuid(diskId)}") => diskGolfDiskController.getDiskGolfDisk(DiskGolfDiskId(diskId))

    // Disk golf baskets
    case POST(p"/disk-golf-baskets") => diskGolfBasketController.createDiskGolfBasket
    case GET(p"/disk-golf-baskets")  => diskGolfBasketController.getDiskGolfBaskets
    case GET(p"/disk-golf-baskets/${uuid(basketId)}") =>
      diskGolfBasketController.getDiskGolfBasket(DiskGolfBasketId(basketId))

    // Disk golf games
    case POST(p"/disk-golf-games")                => diskGolfGameController.createDiskGolfGame
    case GET(p"/disk-golf-games")                 => diskGolfGameController.getDiskGolfGames
    case GET(p"/disk-golf-games/${uuid(gameId)}") => diskGolfGameController.getDiskGolfGame(DiskGolfGameId(gameId))
    case POST(p"/disk-golf-games/${uuid(gameId)}/start") =>
      diskGolfGameController.startDiskGolfGame(DiskGolfGameId(gameId))
    case POST(p"/disk-golf-games/${uuid(gameId)}/finish") =>
      diskGolfGameController.finishDiskGolfGame(DiskGolfGameId(gameId))
  }
}
