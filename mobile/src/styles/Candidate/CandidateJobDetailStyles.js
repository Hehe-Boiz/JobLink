import {StyleSheet, Dimensions} from 'react-native';

const {width} = Dimensions.get('window');
export default StyleSheet.create({
    container: {
        paddingBottom: 20,
    },
    headerNav: {
        flexDirection: "row",
        justifyContent: "space-between",
        marginBottom: 20,
        paddingHorizontal: 15,
        paddingTop: 10,
    },
    contentLogoContainer: {
        marginTop: 50,
        alignItems: "center",
        backgroundColor: "#f8f7f7",
        paddingBottom: 20,
    },
    logo: {
        width: 60,
        height: 60,
        resizeMode: "contain"
    },
    logoWrapper: {
        width: 90,
        height: 90,
        borderRadius: 50,
        backgroundColor: "#AFECFE",
        justifyContent: "center",
        alignItems: "center",
        marginBottom: 16,
        elevation: 3,
        alignSelf: 'center',
        marginTop: -40

    },
    section: {
        paddingBottom: 20
    },
    jobTitle: {
        fontSize: 18,
        color: "#0D0140",
        fontWeight: 700,
        marginBottom: 16
    },
    infoRow: {
        flexDirection: "row",
        alignItems: 'center',
        gap: 2
    },
    infoText: {
        fontSize: 17,
        color: '#524B6B',
        fontWeight: 400,
    },
    dot: {
        width: 5,
        height: 5,
        borderRadius: 2,
        backgroundColor: '#524B6B',
        marginHorizontal: 10,
    },
    containerJob: {
        marginTop: 10,
        paddingHorizontal: 20,
        color: "#524B6B"
    },
    row: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        marginBottom: 12,
    },
    bulletContainer: {
        width: 24,
        alignItems: 'center',
    },
    bullet: {
        fontSize: 24,
        color: '#524B6B',
        lineHeight: 24,
        marginTop: -4,
    },
    textContainer: {
        flex: 1,
    },
    contentReq: {
        fontSize: 14,
        color: '#524B6B',
        lineHeight: 22,
    },
    contentTitle: {
        color: "#150B3D",
        fontWeight: 600,
        fontSize: 16,
        marginBottom: 15
    },
    btnRead: {
        padding: 12,
        borderRadius: 8,
        backgroundColor: "#c8bdf8",
        color: "#0D0140"
    },
    btnContainerRead: {
        marginTop: 15,
        alignItems: "flex-start",
        width: '100%',
        marginBottom: 25
    },
    btnOptionDesCom: {
        flexDirection: "row",
        justifyContent: "space-between",
        paddingHorizontal: 15,
    },
    tabContainer: {
        flexDirection: 'row',
        backgroundColor: '#F5F6FA',
        borderRadius: 12,
        padding: 4,
        marginHorizontal: 20,
        marginVertical: 20,
        height: 50,
    },
    tabButton: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 10,
    },

    activeTab: {
        backgroundColor: '#FFFFFF',
        shadowColor: "#000",
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.1,
        shadowRadius: 3,
        elevation: 3,
    },

    tabText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#95969D',
    },
    activeTabText: {
        color: '#130160',
        fontWeight: 'bold',
    },
    mapContainer: {
        height: 160,
        width: '100%',
        borderRadius: 20,
        overflow: 'hidden',
        position: 'relative',
        borderWidth: 1,
        borderColor: '#F0F0F0'
    },
    mapImage: {
        width: '100%',
        height: '100%',
    },
    pinOverlay: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'center',
        alignItems: 'center',
    },
    pinImage: {
        width: 30,
        height: 30,
    },
    buttonGG: {
        marginTop: 20,
        backgroundColor: '#F5F6FA',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        borderRadius: 12,
    },
    buttonIconGG: {
        width: 20,
        height: 20,
        marginRight: 10
    },
    buttonTextGG: {
        fontSize: 14,
        fontWeight: '600',
        color: '#1A1D1F'
    },
    mb_10: {
        marginBottom: 10
    },
    mb_20: {
        marginBottom: 20
    },

    containerInfoItem: {
        marginBottom: 15,
    },
    titleInfoItem: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#0D0140',
        marginBottom: 8,
    },
    valueInfoItem: {
        fontSize: 14,
        color: '#524B6B',
        lineHeight: 20,
    },
    separatorInfoItem: {
        height: 1,
        backgroundColor: '#EAEAEA',
        marginTop: 15,
    },
    tabContainerContainer: {},
    infoItemContainer: {
        marginBottom: 15,
    },
    infoItemTitle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#0D0140',
        marginBottom: 8,
    },
    infoItemValue: {
        fontSize: 14,
        color: '#524B6B',
        lineHeight: 20,
    },
    infoItemSeparator: {
        height: 1,
        backgroundColor: '#EAEAEA',
        marginTop: 15,
    },
    textAbout: {
        marginBottom: 10
    },
    linkWeb: {
        color: "#7551FF"
    },
    mt_10: {
        marginTop: 10
    },
    mt_20: {
        marginTop: 20
    },
    // gallery
    gallerySection: {
        marginTop: 20,
    },
    galleryContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 15,
    },
    galleryItem: {
        flex: 1,
        height: 130,
        borderRadius: 12,
        overflow: 'hidden',
        position: 'relative',
    },
    galleryImage: {
        width: '100%',
        height: '100%',
    },

    galleryOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    galleryMoreText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    modalContainer: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalCloseButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalImageWrapper: {
        width: width,
        height: '100%',
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalImage: {
        width: '90%',
        height: '80%',
    },
    modalFooter: {
        position: 'absolute',
        bottom: 50,
        left: 0,
        right: 0,
        alignItems: 'center',
    },
    modalHeader: {
        position: 'absolute',
        top: 50,
        left: 0,
        right: 0,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        zIndex: 1000,
    },
    paginationText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    footerHint: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 12,
        letterSpacing: 1,
    }
});